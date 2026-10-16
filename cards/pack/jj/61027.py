from . import *

# Unbreakable Bond
def GetAbilities():
    def bond(effect,message):
        effect.this.RemoveThreatFromSchemes(effect.targets2,3,effect)
        # Selecting one point at a time permits any legal distribution, including 3/0.
        for _ in range(3):
            effect.GetInitiator().ChooseAbilities(effect,AbilityFactory.ForChoiceAbility("Heal 1 damage",
                lambda targets: effect.this.HealthUnits(targets,1,effect))
                .SetTarget(Friend,names=["Jessica Jones","Luke Cage"],canbe_heal=True))
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,bond)
        .SetPlay().SetLabel("thwart").SetTarget("TeamUp").SetTarget2(Scheme2)]
