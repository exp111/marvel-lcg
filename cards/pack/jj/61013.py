from . import *

# Reluctant Flier
def GetAbilities():
    def flier(effect,message):
        message.PreventDamage("All",effect)
        effect.this.DealDamage([effect.GetInitiator().GetIdentity()],1,effect)
    return [AbilityFactory.WhenUnitWouldTakeDamage(AbilityType.HeroInterrupt,"You",flier,
        is_from_attack=True,at_least_damage=3).SetLabel("defense")
        .SetCostFunc(CostFunc.Discard("This"))]
