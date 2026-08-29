from . import *


def GetAbilities() -> Sequence['Ability']:

    def heightened_hearing(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        message.GainATKForThisAttack(-3, effect)
        message.ReplaceTarget(effect.GetInitiator().GetIdentity())

    return [
        AbilityFactory.CanPlayThisUpgradeCard(Enemy),
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.HeroInterrupt,
            "AttachedEnemy",
            heightened_hearing,
        ).SetCostFunc(CostFunc.Discard("This")).SetLabel("defense"),
    ]
