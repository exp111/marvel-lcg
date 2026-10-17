from . import *

# Unbreakable Bond
def GetAbilities():
    def bond(effect,message):
        effect.this.RemoveThreatFromSchemes(effect.targets2,3,effect)
        # Allocate the total before healing, so each character is healed once.
        effect.GetInitiator().ChooseAbilities(effect,
            AbilityFactory.ForChoiceAbility("Distribute 3 healing",
                lambda targets: effect.this.HealthUnits(targets,1,effect))
            .SetTarget(Friend,names=["Jessica Jones","Luke Cage"],canbe_heal=True,
                range=Select.ExactTargetCountUpToAvailable(3),repeat_rules="Sustained"))
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,bond)
        .SetPlay().SetLabel("thwart").SetTarget("TeamUp")
        .SetTarget2(Scheme2,check_fn=lambda effect,face: face.CanBeThwartBy(effect))
        .SetTarget3(Friend,names=["Jessica Jones","Luke Cage"],canbe_heal=True)]
