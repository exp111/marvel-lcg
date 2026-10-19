from . import *

# Shakedown
def GetAbilities():
    def shakedown(effect,message):
        minion=message.who_took_damage.CastTo(Minion)
        amount=minion.base_scheme
        effect.this.RemoveThreatFromSchemes(effect.targets,amount,effect)
    return [AbilityFactory.CanPlayThisUpgradeCard("Players"),
        AbilityFactory.AfterUnitDefeatedUnit(AbilityType.Response,"You",Minion,shakedown,
            is_from_attack=True,has_excess_damage=False,
            conditions=[lambda effect,message: message.who_took_damage.CastTo(Minion).base_scheme > 0])
        .SetCostFunc(CostFunc.Exhaust("This"))
        # Select a legal scheme before paying. This removes threat without
        # thwarting, so patrol does not restrict the response.
        .SetTarget(Scheme2,check_fn=lambda effect,face: face.CanBeThwartBy(effect))
        .SetIgnoreKeyword("Patrol")]
