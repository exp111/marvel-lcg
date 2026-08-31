from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import UnidentifiedImageError

from engine import Engine  # noqa: F401 - establishes the project's import order
from engine.device.web.server import server_files
from engine.device.web.server.server_files import GameServerFiles
from engine.lib import ImageLib


WEBP_BYTES = b"RIFF\x04\x00\x00\x00WEBP"


class TestWebPImageLoading(unittest.TestCase):

    def test_webp_bypasses_pillow_when_its_codec_is_unavailable(self):
        with (
            patch("engine.lib.image_creator.features.check", return_value=False),
            patch("engine.lib.image_creator.Image.open") as open_image,
        ):
            image = ImageLib.TryRotateImage(WEBP_BYTES)

        self.assertEqual(image, WEBP_BYTES)
        open_image.assert_not_called()

    def test_webp_is_passed_through_when_pillow_cannot_decode_it(self):
        with patch(
            "engine.lib.image_creator.Image.open",
            side_effect=UnidentifiedImageError("WEBP support not installed"),
        ):
            image = ImageLib.TryRotateImage(WEBP_BYTES)

        self.assertEqual(image, WEBP_BYTES)

    def test_non_webp_decode_errors_are_not_hidden(self):
        with patch(
            "engine.lib.image_creator.Image.open",
            side_effect=UnidentifiedImageError("invalid image"),
        ):
            with self.assertRaises(UnidentifiedImageError):
                ImageLib.TryRotateImage(b"not an image")

    def test_set_image_response_uses_the_webp_content_type(self):
        server = object.__new__(GameServerFiles)
        server.HeaderCache = {}
        request = SimpleNamespace(path="/sets/1. Core Set")

        with patch.object(server_files.Cache, "LoadImage", return_value=WEBP_BYTES):
            response = server.handle_sets_image(request)

        self.assertEqual(response.body, WEBP_BYTES)
        self.assertEqual(response.content_type, "image/webp")


if __name__ == "__main__":
    unittest.main()
