"""Normal catalog, starter-deck launch and artwork coverage for the two packs."""
import asyncio
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from engine import Engine
from engine.file import Cache, FileManager
from engine.file.artwork import ArtworkManifest
from engine.file.artwork_selection import required_images
from engine.lib import Json
from engine.log import Log, Notify
from cards.database import CardsDB
from game.scene import SceneLoader
from game.scene.replay.operation import CommandDescriptor
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices
from game.world.world_render import WorldRender

ROOT = Path(__file__).resolve().parents[1]
HEROES = (("jj", "jessica_jones", "Jessica Jones", "61001b"),
          ("luke_cage", "luke_cage", "Luke Cage", "62001b"))


class TestPackRegistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep the full database and image links local to this test class so
        # artwork tests with deliberately small fixture catalogs stay isolated.
        stack = contextlib.ExitStack()
        cls.addClassCleanup(stack.close)
        for name in ("papers", "ability_link_cards", "full_link_cards",
                     "sets_cards", "linked_papers", "ability_cache"):
            stack.enter_context(patch.object(CardsDB, name, {}))
        for name, value in (("cards_custom_files", []), ("cards_json_file", ""),
                            ("checksum_ok", True)):
            stack.enter_context(patch.object(CardsDB, name, value))
        stack.enter_context(patch.object(Cache, "link_pic", {}))
        initialize_database()

    def test_normal_catalog_contains_all_reviewed_faces_and_reprint_links(self):
        reference=json.loads((ROOT/"data/experimental/jj_luke/cards.json").read_text(encoding="utf-8"))
        for pack,cards in reference.items():
            for card in cards:
                with self.subTest(card=card["card_id"]):
                    paper=CardsDB.papers[card["card_id"]]
                    self.assertEqual(paper.pack,"fne" if card["card_id"] in ("61028","62022") else pack)
                    if card["card_id"] in ("62025","62026","62027"):
                        self.assertEqual(len(paper.desc["RES"]),2)
                    else:
                        self.assertTrue(CardsDB.FindAbilities(paper.card_id,paper.pack,paper.set_name))
                    if "ability_link" in card:
                        self.assertEqual(CardsDB.ability_link_cards[paper.card_id],card["ability_link"])

    def test_catalog_checksums_and_pack_menu_entries(self):
        for path in ("data/cards.json","data/sets_info.json"):
            _,status=Json.LoadInternal(str(ROOT/path))
            self.assertEqual(status,"Ok")
        sets=json.loads((ROOT/"data/sets_info.json").read_text())
        for number,(pack,slug,name,_) in zip((61,62),HEROES):
            entry=sets[f"{number}. {name}"]
            self.assertEqual(entry["name"],pack)
            self.assertEqual(entry["heroes"],[slug])

    def test_starter_decks_match_reviewed_40_card_lists(self):
        for pack,slug,name,_ in HEROES:
            path=Path(FileManager.FindJsonPath("Hero",slug))
            self.assertEqual(path.resolve(),ROOT/f"deck/starter/{slug}.json")
            deck=json.loads(path.read_text())
            reference=json.loads((ROOT/f"data/experimental/jj_luke/{pack}-deck.json").read_text())
            self.assertEqual(deck["name"],name)
            self.assertEqual(len(deck["hero_deck"])+len(deck["player_deck"]),40)
            for key in ("hero","hero_deck","player_deck","obligations","nemesis_set","aspect"):
                self.assertEqual(deck[key],reference[key])

    def test_nemesis_sets_are_registered_for_normal_selection(self):
        for _,slug,name,_ in HEROES:
            deck=json.loads((ROOT/f"deck/starter/{slug}.json").read_text())
            path=FileManager.FindJsonPath("EncounterSet",slug+"_nemesis")
            nemesis=json.loads(Path(path).read_text())
            self.assertEqual(nemesis["name"],name+" Nemesis")
            self.assertEqual(nemesis["encounters"],deck["nemesis_set"])
            self.assertEqual(len(nemesis["encounters"]),5)

    def test_starter_deck_web_listing_includes_both_heroes(self):
        from engine.device.web.server.server_get import GameServerGet
        server=object.__new__(GameServerGet)
        server.HeaderCache={}
        response=asyncio.run(server.list_starter_deck(None))
        listing=response.text
        for _,slug,_,_ in HEROES:
            self.assertIn(slug+".json",listing)

    def run_normal_game(self, heroes, through_round=False):
        scene=SceneLoader.NewScene("rhino",None,heroes,610620)
        scene.campaign.expert=False
        # No experimental metadata loader, injected hero descriptor or test-rule override.
        def choose(prompt):
            self.assertLess(len(devices.prompts),100)
            if prompt.event_name=="WhenPlayerInTurn":
                if not through_round or Engine.game.world.round_id>=2:
                    return None
                return CommandDescriptor()
            return CommandDescriptor() if prompt.show_cancel else HeadlessDeviceManager._DefaultChoice(prompt)
        devices=HeadlessDeviceManager(choice_provider=choose)
        with (contextlib.redirect_stdout(io.StringIO()), patch.object(WorldRender,"ErrorOccurred") as errors,
              patch.object(Log,"Warn") as warnings, patch.object(Notify,"Game") as notices,
              patch.object(Engine,"SaveCrash")):
            game=run_scene_with_devices(scene,devices)
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertIsNotNone(devices.stopped_prompt)
        self.assertEqual(devices.stopped_prompt.event_name,"WhenPlayerInTurn")
        self.assertEqual(game.world.event_manager.timing_occurrences,[])
        return game

    def test_both_normal_starters_launch_and_complete_a_round(self):
        for _,slug,name,identity in HEROES:
            with self.subTest(hero=name):
                game=self.run_normal_game([slug],through_round=True)
                player=game.world.const_players[0]
                self.assertEqual(player.name,name)
                self.assertEqual(player.GetIdentity().paper.card_id,identity)
                self.assertEqual(game.world.round_id,2)
                if slug=="jessica_jones":
                    self.assertIn("61002",[f.paper.card_id for f in player.supports.Get()])

    def test_normal_two_player_setup_offers_unique_partner_removal(self):
        game=self.run_normal_game(["jessica_jones","luke_cage"])
        self.assertEqual([p.GetIdentity().paper.card_id for p in game.world.const_players],["61001b","62001b"])
        for player,missing in zip(game.world.const_players,("61003","62002")):
            active=player.player_deck.Get()+player.hand_cards.Get()
            self.assertNotIn(missing,[f.paper.card_id for f in active])
            # Each printed deck already contains its Team-Up. The optional
            # setup rule removes the unusable signature ally after deckbuilding.
            self.assertEqual(len(active),39)

    def test_artwork_catalog_covers_all_faces_and_normal_launch_dependencies(self):
        manifest=ArtworkManifest.load(ROOT/"data/artwork-manifest.json")
        reference=json.loads((ROOT/"data/experimental/jj_luke/cards.json").read_text(encoding="utf-8"))
        for cards in reference.values():
            for card in cards:
                canonical=manifest.canonical_id(card["card_id"])
                self.assertIn(canonical,manifest.cards)
        for _,slug,_,_ in HEROES:
            scene=SceneLoader.NewScene("rhino",None,[slug],610620)
            for image_id in required_images(scene,manifest.data,kind="scene"):
                self.assertIsNotNone(manifest.canonical_id(image_id),image_id)


if __name__=="__main__":
    unittest.main()
