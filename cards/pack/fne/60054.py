from . import *

# Stand Alone


def GetAbilities() -> Sequence['Ability']:

    def stand_alone(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        Faces.ReadyAll(effect.targets, effect)

    return [
        AbilityFactory.CanPlayThisUpgradeCard(),
        AbilityFactory.WhenUnitAttackYou(
            AbilityType.HeroInterrupt,
            Enemy,
            stand_alone,
            conditions=[
                lambda effect, message:
                    len(effect.GetInitiator().GetControlAllies()) == 0,
            ],
        ).SetCostFunc(CostFunc.Exhaust("This"))
        .SetTarget("YourHero", canbe_ready=True),
    ]
