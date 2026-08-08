import asyncio
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from engine.device.manager.web.manager import WebDeviceManager
from engine.lib import Ver


class TestWebManager(IsolatedAsyncioTestCase):

    def test_versioned_menu_url_uses_the_live_build_version(self):
        self.assertEqual(
            WebDeviceManager.VersionedMenuUrl("127.0.0.1:2345", "1.0.0.6r"),
            "http://127.0.0.1:2345/main?v=1.0.0.6r",
        )

    async def test_startup_waits_for_server_and_opens_versioned_menu(self):
        async def accept_connection(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
        ) -> None:
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(accept_connection, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        old_ui_version = getattr(Ver, "ui_version_str", None)
        Ver.ui_version_str = "1.0.0.6r"

        try:
            with patch("webbrowser.open") as open_browser:
                await WebDeviceManager.OpenVersionedMenu(
                    "127.0.0.1",
                    port,
                    f"127.0.0.1:{port}",
                )

            open_browser.assert_called_once_with(
                f"http://127.0.0.1:{port}/main?v=1.0.0.6r",
                new=2,
            )
        finally:
            if old_ui_version is None:
                del Ver.ui_version_str
            else:
                Ver.ui_version_str = old_ui_version
            server.close()
            await server.wait_closed()


if __name__ == "__main__":
    import unittest

    unittest.main()
