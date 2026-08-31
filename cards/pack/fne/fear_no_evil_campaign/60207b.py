from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect') -> None:
        count = 2 if Worlds.IsExpert(effect) else 1
        for player in Worlds.GetPlayers(effect):
            hand = player.hand_cards.Get()
            discard_count = min(count, len(hand))
            player.AskDiscardFaces(
                hand,
                (discard_count, discard_count),
                effect,
            )

    return [CampaignEnvironmentSetup(setup)]
