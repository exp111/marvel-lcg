from . import *


def GetAbilities() -> Sequence['Ability']:
    def thwart(effect: 'Effect', message: 'Message.WhenUnitWouldThwart') -> None:
        message.trigger.CastTo(Unit2).GainForThisActive(
            effect,
            message,
            thwart=4,
        )

    return [
        AbilityFactory.WhenUnitWouldThwart(
            AbilityType.Interrupt,
            Friend,
            thwart,
            thwarted_scheme=None,
        ).SetCostFunc(
            CostFunc.Counter("This", 1, 'synergy'),
        ).AnyPlayerCanDoThis(),
    ]
