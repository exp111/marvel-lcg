"""Real HTTPS/OS-process recovery checks for the bounded artwork installer.

Uses a disposable local certificate, trusted explicitly by the test sessions.
Production TLS validation and the HTTPS-only manifest rule stay enabled.
"""
from copy import deepcopy
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import multiprocessing
from pathlib import Path
import random
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
from time import monotonic, sleep
import unittest
import zipfile

from PIL import Image
import requests

from engine import Engine  # noqa: F401 - establishes project import order
from engine.file import artwork


def network_fixture(url):
    random_bytes = random.Random(1775).randbytes(512 * 512 * 3)
    output = BytesIO()
    Image.frombytes("RGB", (512, 512), random_bytes).save(output, "PNG")
    image = output.getvalue()
    card = {"sha256": sha256(image).hexdigest(), "bytes": len(image),
            "width": 512, "height": 512, "format": "png", "pack_id": "test"}
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr(artwork.ArtworkManifest.member_name(card), image)
    body = output.getvalue()
    manifest = {"schema_version": 1, "catalog_id": "https-fixture", "release_ready": True,
                "cards": {"00001": card}, "aliases": {},
                "packs": {"test": {"url": url, "sha256": sha256(body).hexdigest(),
                                    "bytes": len(body), "files": ["00001"]}}}
    return manifest, body, image


def wait_status(library, state, timeout=10):
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        result = library.status()
        if result["state"] == state:
            return result
        sleep(0.01)
    raise AssertionError(f"Expected {state}, got {library.status()}")


def process_install(manifest, folder, certificate, result):
    def session():
        value = requests.Session()
        value.verify = certificate
        value.trust_env = False
        return value
    library = artwork.ArtworkLibrary(artwork.ArtworkManifest(manifest), folder, session_factory=session)
    try:
        library.start()
        result.put(wait_status(library, "ready"))
    except Exception as error:
        result.put({"failure": str(error)})
    finally:
        library.shutdown()


class TestArtworkHTTPS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        executable = shutil.which("openssl")
        git_openssl = Path("C:/Program Files/Git/usr/bin/openssl.exe")
        if not executable and git_openssl.is_file():
            executable = str(git_openssl)
        if not executable:
            raise unittest.SkipTest("OpenSSL is required only for this disposable local TLS fixture")
        cls.certs = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.certs.cleanup)
        cls.cert = Path(cls.certs.name) / "cert.pem"
        cls.key = Path(cls.certs.name) / "key.pem"
        subprocess.run([executable, "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", str(cls.key), "-out", str(cls.cert), "-days", "1",
                        "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
                        "-addext", "basicConstraints=critical,CA:TRUE"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.calls = []
        self.mode = "normal"
        self.calls_lock = threading.Lock()
        test = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass
            def do_GET(self):
                with test.calls_lock:
                    test.calls.append(dict(self.headers))
                    number = len(test.calls)
                offset = int(self.headers.get("Range", "bytes=0-").split("=")[1].split("-")[0])
                self.send_response(206 if offset else 200)
                self.send_header("Content-Length", str(len(test.body) - offset))
                if offset:
                    self.send_header("Content-Range", f"bytes {offset}-{len(test.body)-1}/{len(test.body)}")
                self.end_headers()
                if test.mode == "disconnect" and number == 1:
                    self.wfile.write(test.body[:131072])
                    self.wfile.flush()
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                if test.mode == "slow":
                    sleep(0.2)
                self.wfile.write(test.body[offset:])
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(str(self.cert), str(self.key))
        self.server.socket = tls.wrap_socket(self.server.socket, server_side=True)
        self.manifest, self.body, self.image = network_fixture(f"https://127.0.0.1:{self.server.server_port}/test.zip")
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.addCleanup(self.close_server)
        self.libraries = []
        self.addCleanup(lambda: [library.shutdown() for library in self.libraries])

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=2)

    def library(self):
        def session():
            value = requests.Session()
            value.verify = str(self.cert)
            value.trust_env = False
            return value
        library = artwork.ArtworkLibrary(artwork.ArtworkManifest(deepcopy(self.manifest)),
                                         self.root / "library", session_factory=session)
        self.libraries.append(library)
        return library

    def test_real_https_fresh_install_then_offline_reopen(self):
        first = self.library()
        first.start()
        wait_status(first, "ready")
        self.assertEqual(first.get_image("00001"), self.image)
        first.shutdown()
        second = self.library()
        second.start()
        self.assertTrue(second.status()["ready"])
        self.assertEqual(second.get_image("00001"), self.image)
        self.assertEqual(len(self.calls), 1)

    def test_real_disconnect_is_resumed_by_new_library_with_http_range(self):
        self.mode = "disconnect"
        first = self.library()
        first.start()
        wait_status(first, "error")
        self.assertFalse(first.status()["can_play"])
        first.shutdown()
        partial = next((first.root / "downloads").glob("*.part"))
        self.assertEqual(partial.stat().st_size, 131072)
        second = self.library()
        second.start()
        wait_status(second, "ready")
        self.assertEqual(self.calls[1].get("Range"), "bytes=131072-")
        self.assertEqual(second.get_image("00001"), self.image)

    def test_separate_processes_download_shared_pack_only_once(self):
        self.mode = "slow"
        context = multiprocessing.get_context("spawn")
        result = context.Queue()
        processes = [context.Process(target=process_install,
                                     args=(self.manifest, str(self.root / "library"), str(self.cert), result))
                     for _ in range(2)]
        try:
            for process in processes:
                process.start()
            outcomes = [result.get(timeout=15) for _ in processes]
            for outcome in outcomes:
                self.assertTrue(outcome.get("ready"), outcome)
            for process in processes:
                process.join(timeout=5)
                self.assertEqual(process.exitcode, 0)
            self.assertEqual(len(self.calls), 1)
            self.assertEqual(self.library().get_image("00001"), self.image)
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=2)
            result.close()
            result.join_thread()


if __name__ == "__main__":
    unittest.main()
