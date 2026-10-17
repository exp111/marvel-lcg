from . import *

# Luke Cage
def GetAbilities():
    return [AbilityFactory.WhenInYourPlayTurn(
        AbilityType.Action, lambda effect, message: Faces.GiveStatus(effect.targets, "Tough", effect)
    ).SetCostFunc(CostFunc.Exhaust("This")).SetCostFunc(CostFunc.DealDamage(1, "This"))
    .SetTarget("This", canbe_tough=True)]
