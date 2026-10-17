from . import *

# Fogwell's Gym
def GetAbilities():
    return [AbilityFactory.AfterStatusDiscardFrom(AbilityType.Response,
        CardFinder(card_type=Unit2,trait="DEFENDER"),"Tough",
        lambda effect,message: Faces.ReadyAll(effect.targets,effect))
        .SetCostFunc(CostFunc.Exhaust("This")).SetTarget("Trigger",canbe_ready=True)]
