import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from engine.file.cache import (
    CACHE_FOLDER,
    IMAGE_FOLDERS,
    IMAGE_SERVERS,
    TEXTURE_FOLDER,
    Cache,
    ImageLib,
)


class TestIdentityImageMapping(unittest.TestCase):

    IDENTITY_PAIRS = (
        ("16001a", "16001b"),  # Groot
        ("16029a", "16029b"),  # Rocket Raccoon
        ("32001a", "32001b"),  # Colossus
        ("32030a", "32030b"),  # Shadowcat
        ("33001a", "33001b"),  # Cyclops
        ("34001a", "34001b"),  # Phoenix
        ("35001a", "35001b"),  # Wolverine
        ("36001a", "36001b"),  # Storm
        ("37001a", "37001b"),  # Gambit
        ("38001a", "38001b"),  # Rogue
    )

    def test_cerebro_is_the_primary_image_source(self):
        project_root = Path(__file__).resolve().parents[1]
        launch = json.loads((project_root / "launch.json").read_text(encoding="utf-8"))

        self.assertIn(
            "cerebrodatastorage.blob.core.windows.net",
            launch["image_servers"][0],
        )
        self.assertIn("marvelcdb.com", launch["image_servers"][1])

    def test_cerebro_identity_sides_are_swapped_to_match_game_data(self):
        cerebro = (
            "https://cerebrodatastorage.blob.core.windows.net/"
            "cerebro-cards/official/{card_id:U}.jpg"
        )
        marvelcdb = "https://marvelcdb.com/bundles/cards/{card_id}.jpg"

        for hero_id, alter_ego_id in self.IDENTITY_PAIRS:
            with self.subTest(hero_id=hero_id):
                self.assertEqual(Cache.GetRemoteCardId(cerebro, hero_id), alter_ego_id)
                self.assertEqual(Cache.GetRemoteCardId(cerebro, alter_ego_id), hero_id)
                self.assertEqual(Cache.GetRemoteCardId(marvelcdb, hero_id), hero_id)
                self.assertEqual(Cache.GetRemoteCardId(marvelcdb, alter_ego_id), alter_ego_id)

    def test_corrected_faces_do_not_reuse_legacy_disk_cache_names(self):
        for hero_id, alter_ego_id in self.IDENTITY_PAIRS:
            with self.subTest(hero_id=hero_id):
                self.assertEqual(
                    Cache.GetCacheFileName(hero_id),
                    f"normalized-identity-sides/{hero_id}",
                )
                self.assertEqual(
                    Cache.GetCacheFileName(alter_ego_id),
                    f"normalized-identity-sides/{alter_ego_id}",
                )

        self.assertEqual(Cache.GetCacheFileName("01001a"), "01001a")

    def test_load_image_bypasses_legacy_reversed_file(self):
        cerebro = (
            "https://cerebrodatastorage.blob.core.windows.net/"
            "cerebro-cards/official/{card_id:U}.jpg"
        )
        response = Mock()
        response.content = b"normalized hero image"
        response.headers = {"Content-Type": "image/jpeg"}
        response.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pics = root / "pics"
            textures = root / "textures"
            cache = root / "cache"
            pics.mkdir()
            textures.mkdir()
            cache.mkdir()
            (cache / "32001a.jpg").write_bytes(b"legacy alter-ego image")

            Cache.cache.clear()
            with (
                patch.object(IMAGE_FOLDERS, "value", [str(pics)]),
                patch.object(TEXTURE_FOLDER, "value", str(textures)),
                patch.object(CACHE_FOLDER, "value", str(cache)),
                patch.object(IMAGE_SERVERS, "value", [cerebro]),
                patch("engine.file.cache.requests.get", return_value=response) as get,
                patch.object(ImageLib, "TryRotateImage", side_effect=lambda data: data),
            ):
                image = Cache.LoadImage("32001a")

            self.assertEqual(image, b"normalized hero image")
            self.assertIn("/32001B.jpg", get.call_args.args[0])
            self.assertEqual(
                (cache / "normalized-identity-sides" / "32001a.jpg").read_bytes(),
                b"normalized hero image",
            )
            self.assertEqual(
                (cache / "32001a.jpg").read_bytes(),
                b"legacy alter-ego image",
            )


if __name__ == "__main__":
    unittest.main()
