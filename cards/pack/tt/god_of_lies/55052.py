from . import *


def GetAbilities() -> Sequence['Ability']:
    def attack(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        message.trigger.CastTo(Unit2).GainForThisActive(
            effect,
            message,
            attack=4,
        )

    return [
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.Interrupt,
            Friend,
            attack,
        ).SetCostFunc(
            CostFunc.Counter("This", 1, 'synergy'),
        ).AnyPlayerCanDoThis(),
    ]
