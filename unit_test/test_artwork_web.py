from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from engine import Engine  # establishes the project's import order
from engine.file import Cache
from engine.device.web.server.server_base import GameServerBase
from engine.device.web.server.server_new_game import GameServerNewGame
from engine.device.web.server.server import GameServer
from engine.lib import Ver
from game.scene.scene import Scene
from game.scene.replay.campaign import CampaignDescriptor
from game.scene.loader import SceneLoader
from cards.database import CardsDB
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer


class TestArtworkWeb(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.status = {'state': 'downloading', 'can_play': False, 'ready': False}
        self.status_patch = patch.object(Cache, 'GetArtworkStatus', side_effect=lambda: self.status)
        self.status_patch.start()
        self.addCleanup(self.status_patch.stop)
        self.server = GameServerBase()
        self.game = SimpleNamespace(world=None)
        self.server.device_manager = SimpleNamespace(controllers=[SimpleNamespace(game=self.game)])
        self.server.IsAuthenticate = Mock(return_value=True)
        self.server.IsVersionMatch = Mock(return_value=True)
        self.calls = []

        async def handler(request):
            self.calls.append(request.path)
            return web.Response(text='page or mutation')

        self.server.AddAwaitGetSecurity('/get_artwork_status', self.server.artwork_status)
        self.server.AddPostSecurity('/artwork_action', self.server.artwork_action)
        self.server.web_app.router.add_route('*', '/{path:.*}', handler)
        self.client = TestClient(TestServer(self.server.web_app))
        await self.client.start_server()
        self.addAsyncCleanup(self.client.close)

    async def test_initial_preparation_cannot_be_bypassed_by_direct_pages(self):
        for path in ['/main', '/deck', '/cards', '/scene', '/replay', '/puzzle',
                     '/public/deck.html', '/public//deck.html', '//public/deck.html',
                     '/public%5Cdeck.html',
                     '/public/marvel.html', '/watch', '/?p=0']:
            with self.subTest(path=path):
                if path.startswith('//'):
                    response = await self.client.session.get(str(self.client.make_url('/')).rstrip('/') + path, allow_redirects=False)
                else:
                    response = await self.client.get(path, allow_redirects=False)
                self.assertEqual(response.status, 303)
                self.assertTrue(response.headers['Location'].startswith('/artwork?next='))
        self.assertEqual(self.calls, [])

    async def test_start_and_load_are_rejected_before_handler_mutation(self):
        for method, path in [('get', '/new'), ('get', '/load_replay'), ('get', '/resume_replay'),
                             ('post', '/load_replay_data'), ('get', '/new_puzzle')]:
            response = await getattr(self.client, method)(path)
            self.assertEqual(response.status, 409)
            self.assertEqual((await response.json())['artwork_url'], '/artwork')
        self.assertEqual(self.calls, [])
        # POST security does not require the version cookie: its absence may
        # not bypass first-time preparation either.
        self.server.IsVersionMatch.return_value = False
        self.assertEqual((await self.client.post('/load_replay_data')).status, 409)
        self.assertEqual(self.calls, [])

    async def test_preparation_credits_and_diagnostics_remain_accessible(self):
        for path in ['/artwork', '/credits', '/report']:
            self.assertEqual((await self.client.get(path)).status, 200)
        response = await self.client.get('/get_artwork_status')
        self.assertEqual(await response.json(), self.status)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    async def test_running_game_is_not_interrupted_by_a_failed_update(self):
        self.game.world = object()
        self.status['state'] = 'error'
        for path in ['/?p=0', '/watch', '/public/marvel.html']:
            self.assertEqual((await self.client.get(path)).status, 200)
        self.assertEqual((await self.client.get('/new')).status, 409)

    async def test_previous_ready_catalog_keeps_existing_content_available(self):
        self.status.update(can_play=True, has_previous=True)
        self.assertEqual((await self.client.get('/deck')).status, 200)

    async def test_controls_require_authentication_same_origin_and_fixed_action(self):
        library = SimpleNamespace(pause=Mock(), resume=Mock(), retry=Mock())
        origin = str(self.client.make_url('/').origin())
        with patch.object(Cache, 'GetArtworkLibrary', return_value=library):
            response = await self.client.post('/artwork_action', json={'action': 'pause'})
            self.assertEqual(response.status, 403)
            response = await self.client.post('/artwork_action', json={'action': 'pause'}, headers={'Origin': 'https://elsewhere.invalid'})
            self.assertEqual(response.status, 403)
            for data in [{'action': 'clear'}, {'action': 'resume', 'url': 'https://elsewhere.invalid'}, {'action': []}]:
                response = await self.client.post('/artwork_action', json=data, headers={'Origin': origin})
                self.assertEqual(response.status, 400)
            response = await self.client.post('/artwork_action', json={'action': 'pause'}, headers={'Origin': origin})
            self.assertEqual(response.status, 200)
            library.pause.assert_called_once()
            self.server.IsAuthenticate.return_value = False
            response = await self.client.post('/artwork_action', json={'action': 'resume'}, headers={'Origin': origin})
            self.assertEqual(response.status, 401)
            library.resume.assert_not_called()

    async def test_cloudflare_https_origin_is_accepted_by_http_host(self):
        library = SimpleNamespace(pause=Mock())
        with patch.object(Cache, 'GetArtworkLibrary', return_value=library):
            response = await self.client.post('/artwork_action', json={'action': 'pause'}, headers={
                'Host': 'game.trycloudflare.com', 'Origin': 'https://game.trycloudflare.com',
            })
        self.assertEqual(response.status, 200)
        library.pause.assert_called_once()

    async def test_actual_routes_bootstrap_version_cookie_then_show_preparation(self):
        server = GameServer(SimpleNamespace(controllers=[]))
        actual = TestClient(TestServer(server.web_app))
        await actual.start_server()
        self.addAsyncCleanup(actual.close)
        with patch.object(Ver, 'ui_version_str', 'test-artwork', create=True):
            first = await actual.get('/main', allow_redirects=False)
            self.assertIn('get_version', await first.text())
            version = await actual.get('/get_version')
            self.assertEqual(version.cookies['app_version'].value, 'test-artwork')
            headers = {'Cookie': 'app_version=test-artwork'}
            main = await actual.get('/main', headers=headers, allow_redirects=False)
            self.assertEqual(main.status, 303)
            preparation = await actual.get('/artwork', headers=headers)
            self.assertIn('Prepare card artwork', await preparation.text())
            status = await actual.get('/get_artwork_status', headers=headers)
            self.assertEqual(await status.json(), self.status)
            credits = await actual.get('/credits', headers=headers)
            self.assertEqual(credits.status, 200)

    async def test_selected_artwork_is_checked_before_campaign_settings_or_game_change(self):
        server = object.__new__(GameServerNewGame)
        server.device_manager = SimpleNamespace(controllers=[SimpleNamespace(game=Mock())])
        descriptor = object()
        request = SimpleNamespace(rel_url=SimpleNamespace(query={'data': '{}'}))
        with (patch('engine.device.web.server.server_new_game.Json.LoadsAs', return_value=descriptor),
              patch.object(Cache, 'ArtworkReadyForSelection', return_value=False) as ready,
              patch('engine.device.web.server.server_new_game.CampaignSettings.UpdateForLaunch') as save):
            response = await server.new_game(request)
        self.assertEqual(response.status, 409)
        ready.assert_called_once_with('new_game', descriptor)
        save.assert_not_called()
        server.game.NewGame.assert_not_called()

    async def test_actual_load_route_accepts_migrated_scene_and_checks_before_session_mutation(self):
        self.status.update(can_play=True)
        game = Mock()
        manager = SimpleNamespace(controllers=[SimpleNamespace(game=game, manager=Mock())])
        server = GameServer(manager)
        actual = TestClient(TestServer(server.web_app))
        await actual.start_server()
        self.addAsyncCleanup(actual.close)
        scene = Scene(version='1.3.3', campaign=CampaignDescriptor(villain=['01094']))
        scene.UpdateVersion()
        library = Mock()
        library.status.return_value = self.status
        library.manifest = SimpleNamespace(data={'cards': {'01094': {}}})
        library.ready_for.return_value = False
        with (patch.object(Ver, 'ui_version_str', 'test-artwork', create=True),
              patch.object(Cache, 'GetArtworkLibrary', return_value=library),
              patch.object(Cache, 'HasLocalImage', return_value=False),
              patch.object(Cache, 'CustomImageServers', return_value=[]),
              patch.object(CardsDB, 'cards_custom_files', []),
              patch.object(SceneLoader, 'Load', return_value=scene)):
            headers = {'Cookie': 'app_version=test-artwork'}
            denied = await actual.get('/resume_replay?fixture.json', headers=headers)
            self.assertEqual(denied.status, 409)
            game.session.Load.assert_not_called()
            library.ready_for.return_value = True
            allowed = await actual.get('/resume_replay?fixture.json', headers=headers)
            self.assertEqual(allowed.status, 200)
            game.session.Load.assert_called_once_with('fixture.json', -1, 'Load')


if __name__ == '__main__':
    unittest.main()
