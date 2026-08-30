from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect') -> None:
        Faces.GiveStatus(
            [player.GetIdentity() for player in Worlds.GetPlayers(effect)],
            "Tough",
            effect,
        )

    return [CampaignEnvironmentSetup(setup)]
