from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        Unused(message)
        Faces.ExhaustAll(GetDailyBugleSupports(effect), effect)

    return [
        *AbilityFactory.CardCannotReady(DAILY_BUGLE_SUPPORT),
        AbilityFactory.WhenThisRevealed(None, revealed),
    ]
