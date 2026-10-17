from . import *

# Defensive Formation
def GetAbilities():
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.Action,
        lambda effect,message: Faces.GiveStatus(effect.targets,"Tough",effect))
        .SetCostFunc(CostFunc.Exhaust("This")).SetCostFunc(CostFunc.Counter("This",1,"block"))
        .SetTarget(Ally,trait="DEFENDER",canbe_tough=True)]
