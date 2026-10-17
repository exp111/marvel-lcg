from . import *

# Mitigated Threat


def GetAbilities():
    def upkeep(effect, message):
        paid = []
        Players.ForEachPlayer(effect, lambda player:
            paid.append(player.AskSpendResources(Cost("1"), effect)))
        if not all(paid):
            Faces.DiscardAll([effect.this], effect)

    return [
        AbilityFactory.CanPlayThisUpgradeCard(CardFace),
        *AbilityFactory.AttachedCardLosesIcons("Acceleration", "Amplify", "Crisis", "Hazard"),
        AbilityFactory.WhenRoundEnd(AbilityType.ForcedResponse, None, upkeep),
    ]
