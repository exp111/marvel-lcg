from core import *
import requests
from math import ceil
from time import monotonic
from urllib.parse import urlsplit
from pathlib import Path
from threading import RLock
import hashlib
import sys
from engine.lib import ImageCreator, ImageLib
from engine.log import Log
from engine.file import FileManager
from engine.config import ConfigVariables

CATEGORY_NAME = "CACHE"

IMAGE_FOLDERS   = ConfigVariables.Folders('image_folders', ["./assets/pics/"])
TEXTURE_FOLDER  = ConfigVariables.Folder('texture_folder', "./assets/textures/")
CACHE_FOLDER    = ConfigVariables.Folder('cache_folder', "./assets/cache/")
IMAGE_SERVERS   = ConfigVariables.ListStr('image_servers', [])
SAVE_EMPTY_IMAGE = ConfigVariables.Bool('save_empty_image', True)
BREAK_WHEN_LOAD_ONLINE_IMAGE = ConfigVariables.Bool('break_when_load_online_image', False)

class Cache:

    _artwork_library = None
    _artwork_lock = RLock()
    # Old launch.json files remain valid, but these stock services no longer
    # participate in artwork delivery. Explicit non-stock providers still do.
    STOCK_IMAGE_HOSTS = frozenset({
        "cerebrodatastorage.blob.core.windows.net", "marvelcdb.com", "www.marvelcdb.com",
    })

    @staticmethod
    def GetArtworkLibrary():
        with Cache._artwork_lock:
            if Cache._artwork_library is None:
                from engine.file.artwork import load_artwork_library
                app_root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
                Cache._artwork_library = load_artwork_library(
                    app_root / "data" / "artwork-manifest.json",
                    legacy_roots=[Path(CACHE_FOLDER.value)],
                )
            return Cache._artwork_library

    @staticmethod
    def InitializeArtwork():
        Cache.GetArtworkLibrary().start()

    @staticmethod
    def GetArtworkStatus():
        return Cache.GetArtworkLibrary().status()

    @staticmethod
    def ArtworkReadyFor(card_ids):
        return Cache.GetArtworkLibrary().ready_for(card_ids)

    @staticmethod
    def ArtworkReadyForSelection(kind, payload):
        from engine.file.artwork_selection import required_images
        from cards.database import CardsDB
        from engine.lib import Json
        library = Cache.GetArtworkLibrary()
        if payload is None or not library.status().get("can_play", False):
            return False
        manifest = library.manifest.data
        required = required_images(payload, manifest, kind=kind)
        official = set().union(*(set(manifest.get(key, {}))
                                 for key in ("cards", "aliases", "generated", "bundled")))
        # Custom definitions already loaded by CardsDB retain their existing
        # local/generated/provider artwork behavior. Do not infer that an
        # unknown official-looking ID is custom merely because it is missing.
        custom = set()
        for path in CardsDB.cards_custom_files:
            definition = Json.Load(path)
            for pack in definition.values():
                for card in pack:
                    identifier = card.get("card_id")
                    if identifier in CardsDB.papers:
                        custom.add(identifier)
                        if card.get("pic_id"):
                            custom.add(card["pic_id"])
        custom_servers = Cache.CustomImageServers()
        for identifier in required:
            if identifier in custom or library.ready_for([identifier]):
                continue
            if identifier in official:
                if Cache.HasLocalImage(identifier):
                    continue
                if custom_servers and Cache.IsManagedImage(identifier):
                    continue
            return False
        return True

    @staticmethod
    def HasLocalImage(card_id):
        visited = set()
        while card_id and card_id not in visited:
            visited.add(card_id)
            for folder in IMAGE_FOLDERS.value + [TEXTURE_FOLDER.value]:
                for extension in (".webp", ".jpg", ".png"):
                    path = Path(folder) / (card_id + extension)
                    try:
                        if path.is_file():
                            ImageLib.TryRotateImage(path.read_bytes())
                            return True
                    except (OSError, ValueError):
                        pass
            card_id = Cache.link_pic.get(card_id)
        return False

    @staticmethod
    def CustomImageServers():
        return [site for site in IMAGE_SERVERS.value
                if urlsplit(site).hostname not in Cache.STOCK_IMAGE_HOSTS]

    @staticmethod
    def IsManagedImage(card_id):
        import re
        return bool(re.fullmatch(r"\d{5}[a-z]?", card_id)) or card_id in Cache.SPECIAL_IMAGE_URLS

    @staticmethod
    def GetImageState(card_id):
        card_id = card_id.lstrip("/")
        visited = set()
        while card_id in Cache.link_pic and card_id not in visited and card_id not in Cache.cache:
            visited.add(card_id)
            card_id = Cache.link_pic[card_id]
        if card_id not in Cache.retry_after:
            return "ready"
        if Cache.IsManagedImage(card_id) and not Cache.CustomImageServers():
            state = Cache.GetArtworkLibrary().image_state(card_id)
            if state == "pending":
                return "pending"
        return "error"

    cache: Dict[str, bytes] = {}
    link_pic: Dict[str, str] = {}
    # A failed download must not make a placeholder permanent for this session.
    retry_after: Dict[str, float] = {}
    host_retry_after: Dict[str, float] = {}
    RETRY_SECONDS = 30
    DOWNLOAD_TIMEOUT = (5, 10)  # Connection and response-body timeouts.

    # Scenario reference cards are not exposed by the numbered card-image
    # providers. Keep their official image locations explicit so they use the
    # same on-disk cache and offline fallback as every other card image.
    SPECIAL_IMAGE_URLS: Dict[str, str] = {
        "shatter_the_illusion": "https://hallofheroeslcg.com/wp-content/uploads/2025/08/shattertheillusion.jpg",
    }

    # These physical cards use Alter-Ego A / Hero B numbering. MarvelCDB
    # normalizes their images to Hero A / Alter-Ego B to match the card data,
    # while Cerebro retains the physical side letters.
    CEREBRO_REVERSED_IDENTITY_SIDES: Dict[str, str] = {
        "16001a": "16001b", "16001b": "16001a",  # Groot
        "16029a": "16029b", "16029b": "16029a",  # Rocket Raccoon
        "32001a": "32001b", "32001b": "32001a",  # Colossus
        "32030a": "32030b", "32030b": "32030a",  # Shadowcat
        "33001a": "33001b", "33001b": "33001a",  # Cyclops
        "34001a": "34001b", "34001b": "34001a",  # Phoenix
        "35001a": "35001b", "35001b": "35001a",  # Wolverine
        "36001a": "36001b", "36001b": "36001a",  # Storm
        "37001a": "37001b", "37001b": "37001a",  # Gambit
        "38001a": "38001b", "38001b": "38001a",  # Rogue
    }

    @staticmethod
    def GetCacheFileName(card_id: str) -> str:
        if card_id in Cache.CEREBRO_REVERSED_IDENTITY_SIDES:
            # Do not reuse files downloaded before the provider-side mapping
            # was corrected. Those files may contain the opposite face.
            return f"normalized-identity-sides/{card_id}"
        return card_id

    @staticmethod
    def GetRemoteCardId(site: str, card_id: str) -> str:
        if "cerebrodatastorage.blob.core.windows.net" in site:
            return Cache.CEREBRO_REVERSED_IDENTITY_SIDES.get(card_id, card_id)
        return card_id

    @staticmethod
    def SetLinkPic(card_id: str, link_to_pic_id: str):
        Cache.link_pic[card_id] = link_to_pic_id

    @staticmethod
    def SetCache(card_id: str, data: bytes):
        Cache.cache[card_id] = data
        Cache.retry_after.pop(card_id, None)

    @staticmethod
    def GetImageRetrySeconds(card_id: str) -> int|None:
        card_id = card_id.lstrip("/")
        visited = set()
        # Linked cards return their source image without their own cache entry.
        while card_id not in Cache.cache and card_id in Cache.link_pic and card_id not in visited:
            visited.add(card_id)
            card_id = Cache.link_pic[card_id]
        deadline = Cache.retry_after.get(card_id)
        if deadline is None:
            return None
        return max(1, ceil(deadline - monotonic()))

    @staticmethod
    def LoadImage(card_id: str) -> bytes:
        # if url in ['enthralled_minion', 'minion', 'ultron_facedown_drone']:
        #     url = 'player'
        card_id = card_id.lstrip("/")

        if card_id in Cache.cache:
            if monotonic() < Cache.retry_after.get(card_id, float('inf')):
                return Cache.cache[card_id]
            Cache.cache.pop(card_id, None)
            Cache.retry_after.pop(card_id, None)

        assert card_id != "", f"{card_id=}"
        file_name = card_id

        check_folders = IMAGE_FOLDERS.value + [TEXTURE_FOLDER.value]
        cache_file_name = Cache.GetCacheFileName(file_name)

        def try_load_image_data(image_data: bytes):
            return ImageLib.TryRotateImage(image_data)

        # Load the image from the cache and images
        def try_load_image_path(file_path: str) -> bytes|None:
            for ext_name in [".webp", ".jpg", ".png"]:
                check_path = file_path + ext_name
                if FileManager.Exists(check_path):
                    try:
                        with FileManager.OpenFile(check_path, read=True, bin=True) as file:
                            return try_load_image_data(file.Read())
                    except (OSError, ValueError) as error:
                        Log.Warn(CATEGORY_NAME, f"Invalid cached image {check_path}: {error}")
            return None

        def try_load_image_name(name: str) -> bytes|None:
            for cache_folder in check_folders:
                file_paths: List[str] = []
                file_paths.append(f"{cache_folder}/{name}")
                for file_path in file_paths:
                    image_data = try_load_image_path(file_path)
                    if image_data:
                        return image_data
            return None

        image_data = try_load_image_name(file_name)
        if image_data:
            Cache.SetCache(file_name, image_data)
            return image_data

        managed = Cache.IsManagedImage(card_id)
        custom_servers = Cache.CustomImageServers()
        if managed and not custom_servers:
            library = Cache.GetArtworkLibrary()
            image_data = library.get_image(card_id)
            if image_data:
                # The library owns validation and revision selection. Avoid
                # pinning an old revision in this process's legacy memory cache.
                state = library.image_state(card_id)
                if state == "ready":
                    Cache.retry_after.pop(card_id, None)
                else:
                    # An earlier verified revision remains playable while its
                    # replacement downloads, but open pages must keep polling.
                    Cache.retry_after[card_id] = monotonic() + (1 if state == "pending" else Cache.RETRY_SECONDS)
                return image_data

        if managed and custom_servers:
            # A provider change must not promote unverified stock cache bytes.
            provider_key = hashlib.sha256("\n".join(custom_servers).encode()).hexdigest()[:16]
            cache_file_name = f"custom-sources/{provider_key}/{cache_file_name}"

        image_data = None if managed and not custom_servers else try_load_image_path(
            FileManager.JoinPath(CACHE_FOLDER.value, cache_file_name)
        )
        if image_data:
            Cache.SetCache(file_name, image_data)
            return image_data

        if file_name in Cache.link_pic:
            image_data = Cache.LoadImage(Cache.link_pic[file_name])
            if image_data:
                return image_data

        def check_is_card_id(s: str):
            import re
            # Pattern to match: four digits followed by a lowercase letter
            pattern = r'^\d{5}[a-z]?$'
            return re.match(pattern, s)

        def save_to_file(file_name: str, ext_name: str, data: bytes):
            file_path = FileManager.JoinPath(CACHE_FOLDER.value, f"{file_name}.{ext_name}")
            FileManager.MakeDir(FileManager.GetDirName(file_path))
            with FileManager.OpenFile(file_path, write=True, bin=True) as file:
                file.Write(data)

        remote_urls: List[str] = []
        if custom_servers and check_is_card_id(card_id):
            for site in custom_servers:
                remote_card_id = Cache.GetRemoteCardId(site, card_id)
                full_url = site.replace('{card_id}', remote_card_id)
                full_url = full_url.replace('{card_id:U}', remote_card_id.upper())
                remote_urls.append(full_url)

        if remote_urls:
            # Load the image from the internet
            skip_break = not BREAK_WHEN_LOAD_ONLINE_IMAGE.value
            if not skip_break:
                Debug.DebugBreak()

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }

            # "https://cerebrodatastorage.blob.core.windows.net/cerebro-cards/official/${card_id}.jpg",
            # "https://marvelcdb.com/bundles/cards/${card_id}.jpg",
            # "https://marvelcdb.com/bundles/cards/${card_id}.png",

            for full_url in remote_urls:
                host = urlsplit(full_url).netloc
                if monotonic() < Cache.host_retry_after.get(host, 0):
                    continue
                try:
                    Log.DebugInfo(CATEGORY_NAME, f"Downloading from {full_url}")

                    response = requests.get(full_url, headers=headers, timeout=Cache.DOWNLOAD_TIMEOUT)
                    response.raise_for_status()
                    data = response.content
                    try:
                        image_data = try_load_image_data(data)
                    except (OSError, ValueError) as error:
                        Log.Warn(CATEGORY_NAME, f"Invalid image downloaded from {full_url}: {error}")
                        continue
                    # Some providers label PNG bytes as JPEG, or vice versa.
                    ext_name = {
                        'image/jpeg': 'jpg',
                        'image/png': 'png',
                        'image/webp': 'webp',
                    }[ImageLib.GetContentType(data)]
                    save_to_file(cache_file_name, ext_name, data)
                    Log.DebugInfo(CATEGORY_NAME, f"Downloaded: {file_name}")
                    Cache.host_retry_after.pop(host, None)
                    Cache.SetCache(file_name, image_data)
                    return image_data
                except requests.exceptions.Timeout:
                    Log.Warn(CATEGORY_NAME, f"Timeout occurred while downloading {file_name}")
                except requests.exceptions.RequestException as e:
                    Log.Warn(CATEGORY_NAME, f"Request failed with error: {e}")
                    if isinstance(e, requests.exceptions.ConnectionError) or (
                        e.response is not None and (e.response.status_code == 429 or e.response.status_code >= 500)
                    ):
                        Cache.host_retry_after[host] = monotonic() + Cache.RETRY_SECONDS

        if managed and custom_servers:
            # Explicit providers keep their precedence over stock artwork.
            # A provider outage can still display verified local artwork while
            # retaining a retry header for the user's chosen provider.
            image_data = Cache.GetArtworkLibrary().get_image(card_id)
            if image_data:
                Cache.SetCache(file_name, image_data)
                Cache.retry_after[file_name] = monotonic() + Cache.RETRY_SECONDS
                return image_data

        # raise Exception(f"Failed to load {file_name} from the internet")
        image_data = ImageCreator.CreateNoImage(
            card_id,
            force_text=card_id in Cache.SPECIAL_IMAGE_URLS,
        )
        # Never write failed remote downloads as artwork: they must be able to
        # recover when the provider or connection returns.
        if SAVE_EMPTY_IMAGE.value and not remote_urls and not managed:
            save_to_file(cache_file_name, "jpg", image_data)
        Cache.SetCache(file_name, image_data)
        if remote_urls or managed:
            delay = 1 if managed and not custom_servers and Cache.GetArtworkLibrary().image_state(card_id) == "pending" else Cache.RETRY_SECONDS
            Cache.retry_after[file_name] = monotonic() + delay
        return image_data
