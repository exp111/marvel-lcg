from . import *


def GetAbilities() -> Sequence['Ability']:

    def radar_sense(effect: 'Effect', message: 'Message.AfterUnitAttackUnit') -> None:
        effect.this.CastTo(Upgrade).DealDamage(
            [message.attacked],
            3,
            effect,
            property=AttackProperty(),
        )

    return [
        AbilityFactory.CanPlayThisUpgradeCard(Enemy),
        AbilityFactory.AfterUnitAttackUnit(
            AbilityType.Response,
            "You",
            "AttachedEnemy",
            radar_sense,
        ).SetCostFunc(CostFunc.Discard("This")).SetLabel("attack"),
    ]
