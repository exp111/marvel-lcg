from threading import Lock
import json

from core import *
from engine.config import ConfigVariables
from engine.file import FileManager
from engine.lib import Json
from engine.log import Log


CATEGORY_NAME = "CAMPAIGN_SETTINGS"
CAMPAIGN_SETTINGS_FILE = ConfigVariables.File(
    "campaign_settings_file",
    "campaign_settings.json",
)


class CampaignSettings:
    _lock = Lock()

    @staticmethod
    def _path(file_path: str|None=None) -> str:
        return file_path or CAMPAIGN_SETTINGS_FILE.value

    @staticmethod
    def _normalize(data: Any) -> Dict[str, Dict[str, str]]:
        if not isinstance(data, dict):
            return {}

        settings: Dict[str, Dict[str, str]] = {}
        for campaign_id, campaign_log in data.items():
            if not isinstance(campaign_id, str) or not isinstance(campaign_log, dict):
                continue
            settings[campaign_id] = {
                str(key): str(value)
                for key, value in campaign_log.items()
                if value is not None
            }
        return settings

    @staticmethod
    def Load(file_path: str|None=None) -> Dict[str, Dict[str, str]]:
        path = CampaignSettings._path(file_path)
        if not FileManager.Exists(path):
            return {}
        try:
            with FileManager.OpenFile(path, read=True) as file:
                return CampaignSettings._normalize(json.loads(file.Read()))
        except Exception as exc:
            Log.Warn(CATEGORY_NAME, f"Could not load {path}: {exc}")
            return {}

    @staticmethod
    def _save(
        settings: Dict[str, Dict[str, str]],
        file_path: str|None=None,
    ) -> None:
        import os

        path = CampaignSettings._path(file_path)
        FileManager.MakeDir(FileManager.GetDirName(path))
        temporary_path = f"{path}.tmp"
        with FileManager.OpenFile(temporary_path, write=True) as file:
            file.Write(json.dumps(settings, indent=4, sort_keys=True))
        os.replace(temporary_path, path)

    @staticmethod
    def Update(
        campaign_id: str,
        campaign_log: Dict[str, str],
        file_path: str|None=None,
    ) -> Dict[str, Dict[str, str]]:
        if not campaign_id:
            return CampaignSettings.Load(file_path)

        with CampaignSettings._lock:
            settings = CampaignSettings.Load(file_path)
            settings[campaign_id] = CampaignSettings._normalize({
                campaign_id: campaign_log,
            }).get(campaign_id, {})
            CampaignSettings._save(settings, file_path)
            return settings

    @staticmethod
    def UpdateForLaunch(
        new_game: 'NewGameDescriptor',
        file_path: str|None=None,
    ) -> Dict[str, Dict[str, str]]:
        campaign = Json.Loads(new_game.campaign_json)
        campaign_id = campaign.get("campaign_id", "") \
            if isinstance(campaign, dict) else ""
        return CampaignSettings.Update(
            str(campaign_id),
            new_game.campaign_log,
            file_path,
        )

    @staticmethod
    def Clear(
        campaign_id: str,
        file_path: str|None=None,
    ) -> Dict[str, Dict[str, str]]:
        if not campaign_id:
            return CampaignSettings.Load(file_path)

        with CampaignSettings._lock:
            settings = CampaignSettings.Load(file_path)
            settings.pop(campaign_id, None)
            CampaignSettings._save(settings, file_path)
            return settings
