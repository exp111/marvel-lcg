from . import *


def GetAbilities() -> Sequence['Ability']:
    def minion_defeated(effect: 'Effect', message: 'Message.WhenUnitBeDefeated') -> None:
        villain = Worlds.FindVillain(effect)
        if villain:
            villain.GiveBoostCard(message.trigger, effect)

    return [
        AbilityFactory.WhenUnitBeDefeated(
            AbilityType.ForcedResponse,
            Minion,
            minion_defeated,
        ),
    ]
