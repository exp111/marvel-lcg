from . import *


def GetAbilities() -> Sequence['Ability']:

    def acute_tactility(effect: 'Effect', message: 'Message2') -> None:
        Faces.ReadyAll([effect.GetInitiator().GetIdentity()], effect)

    def defeated_by_you(effect: 'Effect', message: 'Message2') -> bool:
        return message.defeating_player == effect.GetInitiator()

    def removed_by_you(
        effect: 'Effect',
        message: 'Message.AfterSchemeRemoveThreat',
    ) -> bool:
        return message.GetByPlayer() == effect.GetInitiator()

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
            last_threat=True,
            conditions=[removed_by_you],
        ).SetCostFunc(CostFunc.Discard("This")),
    ]
