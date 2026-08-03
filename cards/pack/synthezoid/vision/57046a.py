from . import *

def GetAbilities() -> Sequence['Ability']:
    return [
        *AbilityFactory.GiveKeywordToAttached(Leader, attack=1),
    ]
