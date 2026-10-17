from . import *

# Power Man
def GetAbilities():
    return [AbilityFactory.AfterStatusDiscardFrom(AbilityType.HeroResponse,
        CardFinder(name="Luke Cage"),"Tough",lambda effect,message: effect.GetInitiator().DrawUp(1,effect))
        .SetCostFunc(CostFunc.Exhaust("This"))]
