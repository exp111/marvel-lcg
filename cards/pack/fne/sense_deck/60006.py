from . import *


def GetAbilities() -> Sequence['Ability']:

    def superior_taste(effect: 'Effect', message: 'Message.AfterUnitThwartScheme') -> None:
        effect.this.CastTo(Upgrade).RemoveThreatFromSchemes(
            [message.scheme],
            2,
            effect,
        )

    return [
        AbilityFactory.CanPlayThisUpgradeCard(Scheme2),
        AbilityFactory.AfterUnitThwartScheme(
            AbilityType.Response,
            "YourIdentity",
            "AttachedScheme",
            superior_taste,
        ).SetCostFunc(CostFunc.Discard("This")).SetLabel("thwart"),
    ]
