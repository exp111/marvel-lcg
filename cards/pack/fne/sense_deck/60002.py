from . import *


def GetAbilities() -> Sequence['Ability']:

    def acute_tactility(effect: 'Effect', message: 'Message2') -> None:
        Faces.ReadyAll([effect.GetInitiator().GetIdentity()], effect)

    def defeated_by_you(effect: 'Effect', message: 'Message2') -> bool:
        return (
            message.defeating_player == effect.GetInitiator()
            and Condition.CheckWhichCard("YourIdentity", message.killer, effect)
        )

    return [
        AbilityFactory.CanPlayThisUpgradeCard(
            CardFinder(card_type=Enemy|Scheme2),
        ),
        AbilityFactory.WhenUnitBeDefeated(
            AbilityType.Interrupt,
            "AttachedEnemy",
            acute_tactility,
            has_defeating_player=True,
            conditions=[defeated_by_you],
        ).SetCostFunc(CostFunc.Discard("This")),
        AbilityFactory.AfterSchemeRemoveThreat(
            AbilityType.Interrupt,
            "AttachedScheme",
            acute_tactility,
            by_who="YourIdentity",
            last_threat=True,
        ).SetCostFunc(CostFunc.Discard("This")),
    ]
