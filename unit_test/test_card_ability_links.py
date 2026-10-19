"""Copied cards inherit abilities through the complete chain of card links."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from engine import Engine  # noqa: F401 - establishes project import order
from cards.database import CardsDB


class TestCardAbilityLinks(unittest.TestCase):
    def setUp(self):
        papers = {
            cid: SimpleNamespace(card_id=cid, pack='test_pack', set_name='Test Set', desc={})
            for cid in ('copy', 'template', 'source')
        }
        for name, value in (('papers', papers), ('ability_cache', {}),
                            ('ability_link_cards', {}), ('full_link_cards', {}),
                            ('cards_custom_files', [])):
            patcher = patch.object(CardsDB, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_full_link_inherits_an_ability_link_and_caches_per_card(self):
        CardsDB.full_link_cards['copy'] = 'template'
        CardsDB.ability_link_cards['template'] = 'source'
        module = SimpleNamespace(GetAbilities=Mock(side_effect=lambda: [object()]))
        with patch('importlib.import_module', return_value=module) as load:
            copied = CardsDB.FindAbilities('copy', 'original_pack', 'Original Set')
            self.assertIs(CardsDB.FindAbilities('copy', 'original_pack', 'Original Set'), copied)
            template = CardsDB.FindAbilities('template', 'test_pack', 'Test Set')
        self.assertIsNot(copied, template)
        self.assertEqual(module.GetAbilities.call_count, 2)
        self.assertTrue(all(call.args == ('cards.pack.test_pack.test_set.source',) for call in load.call_args_list))

    def test_ability_link_can_follow_a_full_link(self):
        CardsDB.ability_link_cards['copy'] = 'template'
        CardsDB.full_link_cards['template'] = 'source'
        module = SimpleNamespace(GetAbilities=Mock(return_value=['ability']))
        with patch('importlib.import_module', return_value=module) as load:
            self.assertEqual(CardsDB.FindAbilities('copy', 'original_pack', 'Original Set'), ['ability'])
        load.assert_called_once_with('cards.pack.test_pack.test_set.source')

    def test_circular_links_fail_without_hanging(self):
        CardsDB.full_link_cards['copy'] = 'template'
        CardsDB.ability_link_cards['template'] = 'copy'
        with self.assertRaisesRegex(AssertionError, 'Circular card ability link from copy'):
            CardsDB.FindAbilities('copy', 'original_pack', 'Original Set')

    def test_full_link_to_unscripted_face_keeps_no_abilities(self):
        CardsDB.full_link_cards['copy'] = 'template'
        CardsDB.full_link_cards['template'] = 'source'
        with patch('importlib.import_module', side_effect=ModuleNotFoundError):
            self.assertEqual(CardsDB.FindAbilities('copy', 'original_pack', 'Original Set'), [])


if __name__ == '__main__':
    unittest.main()
