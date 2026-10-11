from contextlib import ExitStack
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
from unittest.mock import Mock, patch

from PIL import Image

from engine import Engine  # noqa: F401 - project's import order
from cards.database import CardsDB
from engine.file import cache as module
from engine.file.cache import Cache
from engine.file.artwork_selection import required_images
from engine.file.manager import ENCOUNTER_SETS_FOLDERS
from engine.lib import Ver
from game.scene.scene import Scene
from game.scene.replay.campaign import CampaignDescriptor


def scan(color):
    output = BytesIO()
    Image.new("RGB", (8, 12), color).save(output, "JPEG")
    return output.getvalue()


class TestArtworkIntegration(unittest.TestCase):
    def setUp(self):
        stack = self.stack = ExitStack()
        self.addCleanup(stack.close)
        self.root = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        self.pics = self.root / "pics"
        self.pics.mkdir()
        self.legacy = self.root / "cache"
        self.legacy.mkdir()
        self.library = Mock()
        self.library.get_image.return_value = None
        self.library.status.return_value = {"state": "downloading"}
        self.library.image_state.return_value = "pending"
        stack.enter_context(patch.object(Cache, "GetArtworkLibrary", return_value=self.library))
        for name in ("cache", "link_pic", "retry_after", "host_retry_after"):
            stack.enter_context(patch.object(Cache, name, {}))
        for var, value in ((module.IMAGE_FOLDERS, [str(self.pics)]),
                           (module.TEXTURE_FOLDER, str(self.root / "textures")),
                           (module.CACHE_FOLDER, str(self.legacy)),
                           (module.IMAGE_SERVERS, [
                               "https://cerebrodatastorage.blob.core.windows.net/cerebro-cards/official/{card_id:U}.jpg",
                               "https://marvelcdb.com/bundles/cards/{card_id}.jpg"]),
                           (module.SAVE_EMPTY_IMAGE, True)):
            stack.enter_context(patch.object(var, "value", value))
        self.now = 0
        stack.enter_context(patch.object(module, "monotonic", side_effect=lambda: self.now))
        self.placeholder = scan("gray")
        stack.enter_context(patch.object(module.ImageCreator, "CreateNoImage", return_value=self.placeholder))
        self.network = stack.enter_context(patch.object(module.requests, "get"))

    def test_unverified_white_tiger_is_preserved_but_never_served(self):
        old = scan("red")
        (self.legacy / "21013.jpg").write_bytes(old)
        self.assertEqual(Cache.LoadImage("21013"), self.placeholder)
        self.assertEqual(Cache.GetImageState("21013"), "pending")
        self.assertEqual(Cache.GetImageRetrySeconds("21013"), 1)
        self.assertEqual((self.legacy / "21013.jpg").read_bytes(), old)
        self.network.assert_not_called()
        clean = scan("blue")
        self.library.get_image.return_value = clean
        self.library.image_state.return_value = "ready"
        self.now = 1.1
        self.assertEqual(Cache.LoadImage("21013"), clean)
        self.assertEqual(Cache.GetImageState("21013"), "ready")
        self.assertEqual((self.legacy / "21013.jpg").read_bytes(), old)

    def test_local_override_precedes_managed_artwork(self):
        art = scan("green")
        (self.pics / "21013.png").write_bytes(art)
        self.assertEqual(Cache.LoadImage("21013"), art)
        self.library.get_image.assert_not_called()
        self.network.assert_not_called()

    def test_previous_revision_stays_visible_until_replacement_is_ready(self):
        old, new = scan("red"), scan("blue")
        self.library.get_image.return_value = old
        self.assertEqual(Cache.LoadImage("21013"), old)
        self.assertEqual(Cache.GetImageState("21013"), "pending")
        self.library.get_image.return_value = new
        self.library.image_state.return_value = "ready"
        self.assertEqual(Cache.LoadImage("21013"), new)
        self.assertIsNone(Cache.GetImageRetrySeconds("21013"))

    def test_full_link_uses_source_without_network_or_ability_alias(self):
        art = scan("blue")
        Cache.SetLinkPic("99111", "21013")
        self.library.get_image.side_effect = lambda key: art if key == "21013" else None
        self.assertEqual(Cache.LoadImage("99111"), art)
        self.network.assert_not_called()

    def test_custom_provider_survives_old_stock_configuration(self):
        custom = "https://my-art.example/cards/{card_id}.jpg"
        with patch.object(module.IMAGE_SERVERS, "value", module.IMAGE_SERVERS.value + [custom]):
            self.assertEqual(Cache.CustomImageServers(), [custom])

    def test_explicit_custom_provider_precedes_ready_official_artwork(self):
        custom = "https://my-art.example/cards/{card_id}.jpg"
        art = scan("green")
        self.network.return_value = Mock(content=art)
        self.library.get_image.return_value = scan("blue")
        with patch.object(module.IMAGE_SERVERS, "value", [custom]):
            self.assertEqual(Cache.LoadImage("21013"), art)
        self.assertEqual(self.network.call_args.args[0], custom.replace("{card_id}", "21013"))
        self.library.get_image.assert_not_called()

    def test_custom_provider_failure_uses_verified_image_and_retries_provider(self):
        custom = "https://my-art.example/cards/{card_id}.jpg"
        art = scan("blue")
        self.network.side_effect = module.requests.ConnectionError("offline")
        self.library.get_image.return_value = art
        with patch.object(module.IMAGE_SERVERS, "value", [custom]):
            self.assertEqual(Cache.LoadImage("21013"), art)
            self.assertEqual(Cache.GetImageState("21013"), "error")
            self.assertEqual(Cache.GetImageRetrySeconds("21013"), Cache.RETRY_SECONDS)
            self.assertEqual(Cache.LoadImage("21013"), art)
        self.network.assert_called_once()

    def configure_selection(self, official):
        self.library.status.return_value = {"can_play": True}
        self.library.manifest = SimpleNamespace(data={"cards": dict.fromkeys(official)})
        self.library.ready_for.return_value = False
        self.stack.enter_context(patch.object(CardsDB, "cards_custom_files", []))
        self.stack.enter_context(patch.object(CardsDB, "papers", {}))
        self.stack.enter_context(patch.object(ENCOUNTER_SETS_FOLDERS, "value", []))

    def test_selection_accepts_valid_local_override_but_not_corrupt_or_unknown_art(self):
        self.configure_selection(["21013"])
        (self.pics / "21013.png").write_bytes(b"corrupt")
        self.assertFalse(Cache.ArtworkReadyForSelection("scene", {"hero_deck": ["21013"]}))
        (self.pics / "21013.png").write_bytes(scan("green"))
        self.assertTrue(Cache.ArtworkReadyForSelection("scene", {"hero_deck": ["21013"]}))
        (self.pics / "99999.png").write_bytes(scan("green"))
        self.assertFalse(Cache.ArtworkReadyForSelection("scene", {"hero_deck": ["99999"]}))
        self.network.assert_not_called()

    def test_selection_accepts_custom_provider_only_for_known_official_ids(self):
        self.configure_selection(["21013"])
        with patch.object(module.IMAGE_SERVERS, "value", ["https://custom.example/{card_id}.png"]):
            self.assertTrue(Cache.ArtworkReadyForSelection("scene", {"hero_deck": ["21013"]}))
            self.assertFalse(Cache.ArtworkReadyForSelection("scene", {"hero_deck": ["99999"]}))
        self.network.assert_not_called()

    def test_registered_custom_cards_keep_generated_and_linked_local_artwork(self):
        self.configure_selection(["21013"])
        path = self.root / "custom-cards.json"
        path.write_text(json.dumps({"custom": [
            {"card_id": "99001", "pic_id": "my_hero"}, {"card_id": "my_upgrade"},
        ]}))
        papers = {"99001": SimpleNamespace(pic_id="my_hero"), "my_upgrade": SimpleNamespace(pic_id="")}
        with (patch.object(CardsDB, "cards_custom_files", [str(path)]),
              patch.object(CardsDB, "papers", papers),
              patch.object(Ver, "version", Ver("1.3.3"), create=True),
              patch.object(CardsDB, "linked_papers", {}),
              patch.object(CardsDB, "full_link_cards", {})):
            self.assertTrue(Cache.ArtworkReadyForSelection("scene", {"hero_deck": ["99001", "my_upgrade"]}))
            self.assertFalse(Cache.ArtworkReadyForSelection("scene", {"hero_deck": ["99001", "21013"]}))
        self.network.assert_not_called()

    def test_generated_cards_and_bundled_textures_do_not_need_a_library(self):
        Cache.LoadImage("no_image")
        self.library.get_image.assert_not_called()
        self.assertIsNone(Cache.GetImageRetrySeconds("no_image"))

    def test_selection_collects_faces_nemesis_set_aside_and_linked_images(self):
        (self.root / "test_nemesis.json").write_text(json.dumps({"encounters": ["46025", "46026"]}))
        papers = {
            "46001a": SimpleNamespace(pic_id=""), "46001b": SimpleNamespace(pic_id=""),
            "46002": SimpleNamespace(pic_id=""), "46025": SimpleNamespace(pic_id=""),
            "46026": SimpleNamespace(pic_id=""), "60050": SimpleNamespace(pic_id="60049"),
        }
        manifest = {"cards": dict.fromkeys(papers), "dependencies": {"fear_no_evil": ["60215"]}}
        with (patch.object(CardsDB, "papers", papers),
              patch.object(CardsDB, "linked_papers", {"46001a": ["46002"]}),
              patch.object(CardsDB, "full_link_cards", {}),
              patch.object(ENCOUNTER_SETS_FOLDERS, "value", [str(self.root)])):
            required = required_images({
                "hero_json": [json.dumps({"hero": ["46001a"], "nemesis_set": ["test_nemesis"]})],
                "campaign_json": json.dumps({"campaign_id": "fear_no_evil", "set_aside": ["60050"]}),
            }, manifest)
        self.assertEqual(required, {"46001a", "46001b", "46002", "46025", "46026", "60050", "60049", "60215"})

    def test_unknown_named_set_cannot_pass_as_empty_content(self):
        with (patch.object(CardsDB, "papers", {}), patch.object(ENCOUNTER_SETS_FOLDERS, "value", [])):
            self.assertIn("unresolved-set:missing", required_images({"encounter_sets": ["missing"]}, {}))

    def test_save_comments_and_names_are_not_card_references(self):
        with (patch.object(CardsDB, "papers", {}), patch.object(ENCOUNTER_SETS_FOLDERS, "value", [])):
            self.assertEqual(required_images({"metadata": {"comment": "10000 points"},
                "players": [{"name": "Sam 12345", "hero": ["46001a"]}]}, {}), {"46001a"})

    def test_migrated_save_dataclasses_can_be_inspected_after_removed_fields(self):
        scene = Scene(version="1.3.3", campaign=CampaignDescriptor(villain=["01094"]))
        scene.UpdateVersion()
        self.assertFalse(hasattr(scene.campaign, "modular_sets"))
        with patch.object(ENCOUNTER_SETS_FOLDERS, "value", []):
            self.assertEqual(required_images(scene, {}, kind="scene"), {"01094"})

    def test_uploaded_legacy_campaign_uses_migrated_dependencies_without_changing_save(self):
        scene = Scene(version="1.3.3", rules=["mode_campaign"],
                      campaign=CampaignDescriptor(villain=["04057"]))
        manifest = {"dependencies": {"rise_of_red_skull": ["04159a", "04159b"]}}
        with patch.object(ENCOUNTER_SETS_FOLDERS, "value", []):
            self.assertEqual(required_images(scene, manifest, kind="scene"), {"04057", "04159a", "04159b"})
        self.assertEqual(scene.campaign.campaign_id, "")
        self.assertTrue(hasattr(scene.campaign, "modular_sets"))
        self.assertEqual(scene.rules, ["mode_campaign"])

    def test_new_game_checks_effective_encounter_selection_not_replaced_defaults(self):
        for name, identifier in [("standard", "01188"), ("standard_iii", "45001"), ("bomb_scare", "01109")]:
            (self.root / f"{name}.json").write_text(json.dumps({"encounters": [identifier]}))
        descriptor = SimpleNamespace(campaign_json=json.dumps({"version": "1.3.3", "name": "Rhino",
            "villain": ["01094"], "encounter_sets": ["standard"], "modular_sets": ["bomb_scare"]}),
            encounter_set_names=["standard_iii"], hero_json=[], seed=1, rules=[], campaign_log={})
        with (patch.object(ENCOUNTER_SETS_FOLDERS, "value", [str(self.root)]),
              patch.object(Ver, "version", Ver("1.3.3"), create=True)):
            self.assertEqual(required_images(descriptor, {}, kind="new_game"), {"01094", "45001"})
        self.assertEqual(descriptor.rules, [])

    def test_replay_debug_cards_are_collected_without_confusing_object_ids(self):
        payload = {"inputs": [
            {"effect": {"id": ":Puzzle.CreatePlayerCard('21013')"}},
            {"effect": {"id": "e10000 c12345 Attack", "targets": ["c99999 card"]}},
        ], "puzzle": ["Puzzle.CreateHandCards('My card')"]}
        with (patch.object(CardsDB, "papers", {"46002": SimpleNamespace(card_id="46002", name="My card", pic_id="")}),
              patch.object(CardsDB, "linked_papers", {}), patch.object(CardsDB, "full_link_cards", {}),
              patch.object(ENCOUNTER_SETS_FOLDERS, "value", [])):
            self.assertEqual(required_images(payload, {}), {"21013", "46002"})


if __name__ == "__main__":
    unittest.main()
