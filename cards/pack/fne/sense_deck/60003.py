from . import *


def GetAbilities() -> Sequence['Ability']:

    def enhanced_olfaction(effect: 'Effect', message: 'Message2') -> None:
        Worlds.UpdateNextCardPlayCost(
            effect.GetInitiator(),
            -2,
            effect,
            in_this="Phase",
        )

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
            enhanced_olfaction,
            has_defeating_player=True,
            conditions=[defeated_by_you],
        ).SetCostFunc(CostFunc.Discard("This")),
        AbilityFactory.AfterSchemeRemoveThreat(
            AbilityType.Interrupt,
            "AttachedScheme",
            enhanced_olfaction,
            by_who="YourIdentity",
            last_threat=True,
        ).SetCostFunc(CostFunc.Discard("This")),
    ]
