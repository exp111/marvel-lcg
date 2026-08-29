from . import *

# Dance with the Devil


def GetAbilities() -> Sequence['Ability']:

    def play_dance_with_the_devil(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        target = Filter.One(effect.targets2, effect)
        if target:
            effect.this.CastTo(Upgrade).AttachTo2(target, effect)

    def dance_with_the_devil(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        effect.this.CastTo(Upgrade).DealDamage(effect.targets, 3, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.PlayTurnOption,
            play_dance_with_the_devil,
            conditions=[
                lambda effect, message:
                    Condition.FieldHasNotThisUniqueType(effect.this, effect),
            ],
        ).SetPlay()
        .SetTarget("TeamUp")
        .SetTarget2(Enemy, is_optional=False),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            dance_with_the_devil,
        ).SetLabel("attack")
        .SetCostFunc(CostFunc.Discard("This"))
        .SetTarget("AttachedEnemy"),
    ]
