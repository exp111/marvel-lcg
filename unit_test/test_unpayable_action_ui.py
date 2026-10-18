"""Issue #141: unavailable resources must not turn into an unpaid action."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from engine import Engine
from engine.log import Log, Notify
from cards.database import CardsDB
from game.test.headless import HeadlessDeviceManager
from game.test.v18_timing_harness import initialize_database, run_scene_with_devices, validate_file
from game.world.world_render import WorldRender


ROOT = Path(__file__).resolve().parents[1]


class TestUnpayableActionUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which('node')
        compiler = shutil.which('tsc.cmd') or shutil.which('tsc')
        if not cls.node or not compiler:
            raise unittest.SkipTest('Node and TypeScript are required for the client regression')
        cls.output = tempfile.TemporaryDirectory(prefix='marvel-unpayable-action-')
        cls.addClassCleanup(cls.output.cleanup)
        compiled = subprocess.run([compiler, '-p', str(ROOT / 'public/js/tsconfig.json'),
                                   '--outDir', cls.output.name], cwd=ROOT,
                                  capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise AssertionError(compiled.stdout + compiled.stderr)
        database = contextlib.ExitStack()
        cls.addClassCleanup(database.close)
        # Repeated database initialization appends linked reward cards. Replay
        # the original save against a fresh catalog, independent of test order.
        for name in ('papers', 'sets_cards', 'linked_papers', 'ability_cache',
                     'ability_link_cards', 'full_link_cards'):
            database.enter_context(patch.object(CardsDB, name, {}))
        initialize_database()

    def run_client(self, fixture=None):
        command = [self.node, str(ROOT / 'unit_test/unpayable_action_ui.cjs'),
                   str(Path(self.output.name) / 'marvel')]
        if fixture:
            path = Path(self.output.name) / 'prompt.json'
            path.write_text(json.dumps(fixture), encoding='utf-8')
            command.append(str(path))
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_reported_save_replays_and_cannot_submit_the_unpayable_action(self):
        scene = validate_file(ROOT / 'unit_test/fixtures/issue_141.json')
        devices = HeadlessDeviceManager(stop_when=lambda prompt: True)
        with (contextlib.redirect_stdout(io.StringIO()),
              patch('game.test.v18_timing_harness.initialize_database'),
              patch.object(WorldRender, 'ErrorOccurred') as errors,
              patch.object(Log, 'Warn') as warnings, patch.object(Notify, 'Game') as notices):
            game = run_scene_with_devices(scene, devices, load_type='InTesting')
        errors.assert_not_called()
        warnings.assert_not_called()
        notices.assert_not_called()
        self.assertEqual(game.controller_manager.replay.current_step_id, 49)
        self.assertEqual([entry.crc for entry in game.controller_manager.replay.history_inputs],
                         [entry.crc for entry in scene.inputs])
        player = game.world.GetFirstPlayer()
        self.assertTrue(player.GetIdentity().IsExhaust())
        self.assertCountEqual([face.paper.card_id for face in player.hand_cards.Get()],
                             ['13022', '40064', '44053', '05023', '44026', '19022'])
        prompt = devices.stopped_prompt
        option = next(option for option in prompt.options if
                      game.world.object_manager.card_dict[option['bind_id']].face.paper.card_id == '44030')
        self.assertEqual(option['target_payment'], {'0': {'cost': 'R', 'payment': [], 'rule': []}})
        fixture = dict(
            ask=dict(options_json=json.dumps(prompt.options), ability_type=prompt.ability_type,
                     event_name=prompt.event_name, show_cancel=prompt.show_cancel),
            cards=[dict(id=card.object_id, card_id=card.face.paper.card_id, control_player=0,
                        effects=[option['id'] for option in prompt.options if option['bind_id'] == card.object_id],
                        resources=[]) for card in game.world.object_manager.card_dict.values()],
            blocked_card=option['bind_id'],
        )
        self.assertEqual(self.run_client(fixture), {'ok': True})

    def test_payment_submission_and_availability_matrix(self):
        self.assertEqual(self.run_client(), {'ok': True})


if __name__ == '__main__':
    unittest.main()
