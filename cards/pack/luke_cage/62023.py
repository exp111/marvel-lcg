from . import *

# Power Man and Iron Fist
def GetAbilities():
    def power_man(effect,message):
        effect.this.DealDamage(effect.targets2,2,effect)
        effect.GetInitiator().ChooseAbilities(effect,AbilityFactory.ForChoiceAbility("Give a character a tough status card",
            lambda targets: Faces.GiveStatus(targets,"Tough",effect)).SetTarget(Unit2,canbe_tough=True))
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,power_man)
        .SetPlay().SetLabel("attack").SetTarget("TeamUp").SetTarget2(Enemy)]
