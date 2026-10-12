from core import *
from engine.network import WebServer
from aiohttp import web
from engine.device.manager.web.manager import WebDeviceManager
from engine.controller import *
from urllib.parse import urlencode, urlsplit
import posixpath

class GameServerBase(WebServer):

    def __init__(self) -> None:
        super().__init__()
        self.web_app.middlewares.append(self.artwork_gate)

    @web.middleware
    async def artwork_gate(self, request: web.Request, handler):
        """Keep incomplete first-time artwork preparation outside game state."""
        pages = {'main', 'deck', 'cards', 'scene', 'replay', 'puzzle',
                 'puzzle_editor', 'puzzle_test', 'marvel'}
        # Windows resolves backslashes in file routes as directory separators.
        normalized_path = posixpath.normpath('/' + request.path.replace('\\', '/').lstrip('/'))
        page = normalized_path.removeprefix('/public/').strip('/').removesuffix('.html')
        game_page = request.path in {'/', '/watch'}
        starts = {'/new', '/new_debug', '/load_replay', '/resume_replay',
                  '/load_replay_data', '/load_puzzle', '/new_puzzle_replay', '/new_puzzle'}
        if (page not in pages and not game_page and request.path not in starts):
            return await handler(request)
        if not self.IsAuthenticate(request) or (request.method != 'POST' and not self.IsVersionMatch(request)):
            return await handler(request)
        # An artwork update must never evict a running game or its spectators.
        try:
            active_game = self.game.world is not None
        except (AttributeError, IndexError):
            active_game = False
        if active_game and (game_page or page == 'marvel'):
            return await handler(request)
        from engine.file import Cache
        status = Cache.GetArtworkStatus()
        if status.get('can_play', False):
            return await handler(request)
        if request.path in starts:
            return web.json_response({
                'error': 'Card artwork is not ready. Finish preparation before starting this game.',
                'artwork_url': '/artwork', 'artwork': status,
            }, status=409, headers={'Cache-Control': 'no-store'})
        target = '/artwork?' + urlencode({'next': str(request.rel_url)})
        raise web.HTTPSeeOther(target, headers={'Cache-Control': 'no-store'})

    async def artwork_status(self, request: web.Request) -> web.Response:
        from engine.file import Cache
        return web.json_response(Cache.GetArtworkStatus(), headers={'Cache-Control': 'no-store'})

    def ArtworkSelectionResponse(self, kind: str, payload) -> web.Response | None:
        from engine.file import Cache
        if Cache.ArtworkReadyForSelection(kind, payload):
            return None
        return web.json_response({
            'error': 'Artwork for this selection is still being prepared. Your selection has been kept; try again when preparation finishes.',
            'artwork_url': '/artwork', 'artwork': Cache.GetArtworkStatus(),
        }, status=409, headers={'Cache-Control': 'no-store'})

    async def artwork_action(self, request: web.Request) -> web.Response:
        from engine.file import Cache
        # Cloudflare terminates HTTPS before forwarding to this HTTP server;
        # compare the browser origin's authority, without trusting proxy headers.
        origin = urlsplit(request.headers.get('Origin', ''))
        if origin.scheme not in {'http', 'https'} or origin.netloc != request.host:
            return web.json_response({'error': 'A same-origin request is required'}, status=403)
        try:
            data = await request.json()
        except Exception:
            return web.json_response({'error': 'Invalid JSON data'}, status=400)
        if (not isinstance(data, dict) or set(data) != {'action'}
                or not isinstance(data['action'], str)
                or data['action'] not in {'pause', 'resume', 'retry'}):
            return web.json_response({'error': 'Expected pause, resume, or retry'}, status=400)
        library = Cache.GetArtworkLibrary()
        getattr(library, data['action'])()
        return web.json_response(Cache.GetArtworkStatus(), headers={'Cache-Control': 'no-store'})

    def SetManager(self, manager: 'WebDeviceManager'):
        self.device_manager = manager

    def get_player_ids(self, request: web.Request) -> List[int]:
        is_hot_seat = 'hot_seat' in request.rel_url.query
        if is_hot_seat:
            manager = self.controller_manager
            return list(range(manager.total_players))

        p = request.query.get('p', '0')
        if p == '':
            return [0]

        player_ids = p.split(',')
        if player_ids:
            player_ids = [int(id) for id in player_ids]
        else:
            player_ids = [0]
        return player_ids

    def get_first_controller(self, request: web.Request) -> 'Controller':
        player_ids = self.get_player_ids(request)
        player_id = player_ids[0]
        return self.device_manager.controllers[player_id]

    def set_full_search_preference(self, player_id: int, enabled: bool) -> None:
        if player_id < 0 or player_id >= len(self.device_manager.controllers):
            return
        controller = self.device_manager.controllers[player_id]
        controller.SetShowDeckDuringFullSearch(enabled)
        if not enabled:
            self.device_manager.AcknowledgeFullSearchPresentation(player_id)

    @property
    def controller_manager(self):
        controller = self.device_manager.controllers[0]
        return controller.manager

    @property
    def game(self):
        controller = self.device_manager.controllers[0]
        return controller.game

