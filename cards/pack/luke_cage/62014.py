from . import *

# Valkyrie
def GetAbilities():
    def valkyrie(effect,message):
        message.SetBeInstead(effect)
        ally=message.trigger.CastTo(Ally)
        effect.this.HealthUnits([ally],max(0,1-ally.health),effect)
    return [AbilityFactory.WhenUnitWouldBeDefeated(AbilityType.Interrupt,Ally,valkyrie,
        conditions=[lambda effect,message: message.trigger != effect.this])
        .SetCostFunc(CostFunc.Discard("This"))]
