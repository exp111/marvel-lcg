from . import *

def GetAbilities() -> Sequence['Ability']:
    return [
        *AbilityFactory.GiveKeywordToAttached(Leader, scheme=1, stalwart=1),
    ]
