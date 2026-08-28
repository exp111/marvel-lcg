from . import *


def GetAbilities() -> Sequence['Ability']:

    def foggy_nelson(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        effect.this.CastTo(Support).RemoveThreatFromSchemes(effect.targets, 2, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.AlterEgoAction,
            foggy_nelson,
        ).SetCostFunc(CostFunc.Exhaust("This")).SetTarget(Scheme2),
    ]
