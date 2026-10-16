from . import *

# Circumstantial Evidence
from .helpers import PlaceEvidence

def GetAbilities():
    return [AbilityFactory.AfterUnitBeDefeated(AbilityType.Response, Enemy,
        lambda effect,message: PlaceEvidence(effect,1)).SetCostFunc(CostFunc.Exhaust("This"))]
