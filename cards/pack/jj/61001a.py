from . import *

# Jessica Jones
from .helpers import PlaceEvidence

def GetAbilities():
    return [AbilityFactory.AfterUnitUseBasicPower(
        AbilityType.Response, "You", lambda effect, message: PlaceEvidence(effect, 1)
    ).SetName("Gather Evidence")]
