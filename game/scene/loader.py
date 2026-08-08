from core import *
from game.scene import *
from game.scene.replay import *
from engine.lib import Json, Ver
from engine.file import FileManager

CATEGORY_NAME = "SCENE"

class LoaderHelper:

    @staticmethod
    def CreateScene(seed: int, campaign: CampaignDescriptor, players: Sequence[HeroDescriptor], rules: List[str]) -> 'Scene':
        scene = Scene(
            version=str(Ver.version),
            metadata={
                "seed": seed,
            },
            rules=rules,
            campaign=campaign,
            players=players,
            inputs=[]
        )
        scene.UpdateVersion()
        for player in scene.players:
            assert player.name != ""
        return scene

    @staticmethod
    def Loads(file_path: str) -> 'Scene':
        # Log.Debug(f"File: {file_path}")

        scene = Json.LoadAs(file_path, Scene, check_sum="Warn")
        scene.UpdateVersion()

        scene.SetMetadataStr("path", file_path)

        return scene

class SceneLoader:

    ENCOUNTER_SET_FAMILIES = ("standard", "expert")

    @staticmethod
    def GetEncounterSetFamily(encounter_set: str) -> str|None:
        for family in SceneLoader.ENCOUNTER_SET_FAMILIES:
            if encounter_set == family or encounter_set.startswith(f"{family}_"):
                return family
        return None

    @staticmethod
    def MergeEncounterSets(required: Sequence[str], selected: Sequence[str]) -> List[str]:
        """Keep required sets while replacing mutually exclusive difficulty variants."""
        selected_by_family: Dict[str, str] = {}
        for encounter_set in selected:
            family = SceneLoader.GetEncounterSetFamily(encounter_set)
            if family:
                selected_by_family[family] = encounter_set

        merged: List[str] = []
        placed_families: Set[str] = set()

        def append_unique(encounter_set: str) -> None:
            if encounter_set not in merged:
                merged.append(encounter_set)

        for encounter_set in required:
            family = SceneLoader.GetEncounterSetFamily(encounter_set)
            if family and family in selected_by_family:
                if family not in placed_families:
                    append_unique(selected_by_family[family])
                    placed_families.add(family)
            else:
                append_unique(encounter_set)

        for encounter_set in selected:
            family = SceneLoader.GetEncounterSetFamily(encounter_set)
            if family:
                if family in placed_families:
                    continue
                if selected_by_family[family] != encounter_set:
                    continue
                placed_families.add(family)
            append_unique(encounter_set)

        return merged

    @staticmethod
    def NewFromJson(campaign_json: str, encounter_set_names: List[str]|None, hero_jsons: List[str], seed: int, rules: List[str], campaign_log: Dict[str, str]) -> 'Scene':
        players: List[HeroDescriptor] = []
        for hero_text in hero_jsons:
            player = Json.LoadsAs(hero_text, HeroDescriptor)
            player.UpdateVersion()
            players.append(player)

        campaign = Json.LoadsAs(campaign_json, CampaignDescriptor)
        campaign.UpdateVersion()

        if encounter_set_names != None:
            campaign.encounter_sets = SceneLoader.MergeEncounterSets(
                campaign.encounter_sets,
                encounter_set_names,
            )
        else:
            campaign.encounter_sets += campaign.modular_sets

        if campaign_log:
            campaign.campaign_log |= campaign_log

        scene = LoaderHelper.CreateScene(seed, campaign, players, rules)
        return scene

    @staticmethod
    def NewScene(campaign_name: str, encounter_set_names: List[str]|None, hero_names: List[str], seed: int) -> 'Scene':
        heroes_text: List[str] = []
        campaign_text: str = ""

        assert type(campaign_name) is str, f"{campaign_name=}"
        for hero_json in hero_names:
            file_path = FileManager.FindJsonPath('Hero', hero_json)
            assert file_path, f"{file_path=}"
            with FileManager.OpenFile(file_path, read=True) as file:
                heroes_text.append(file.Read())

        file_path = FileManager.FindJsonPath('Campaign', campaign_name)
        assert file_path, f"{file_path=}"
        with FileManager.OpenFile(file_path, read=True) as file:
            campaign_text = file.Read()

        scene = SceneLoader.NewFromJson(campaign_text, encounter_set_names, heroes_text, seed, [], {})
        return scene

    @staticmethod
    def Load(replay: str, nullable: bool=False) -> 'Scene|None':
        file_path = FileManager.FindJsonPath('Replay', replay, nullable=nullable)
        if file_path:
            scene = LoaderHelper.Loads(file_path)
            return scene
        else:
            return None
