from . import *

# Toughen Up
def GetAbilities():
    return [AbilityFactory.AfterUnitUseBasicPower(AbilityType.Response,"You",
        lambda effect,message: Faces.GiveStatus(effect.targets,"Tough",effect),powers=["REC"],
        conditions=[lambda effect,message: message.trigger.health>=message.trigger.base_health])
        .SetCostFunc(CostFunc.Exhaust("This")).SetTarget("YourIdentity",canbe_tough=True)]
