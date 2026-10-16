from . import *

# Leather Jacket
from .helpers import PlaceEvidence

def GetAbilities():
    return [
        *AbilityFactory.GiveKeywordToAttached(CardFinder(name="Jessica Jones"),defense=2),
        AbilityFactory.AfterUnitDefendAgainstAttack(AbilityType.Response,"You",
            lambda effect,message: PlaceEvidence(effect,1)),
    ]
