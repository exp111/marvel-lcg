from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect') -> None:
        count = 2 if Worlds.IsExpert(effect) else 1
        for player in Worlds.GetPlayers(effect):
            player.DealEncounterCards(count, effect)

    return [CampaignEnvironmentSetup(setup)]
