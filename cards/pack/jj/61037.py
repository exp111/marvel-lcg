from . import *

# Innate Inspiration
def GetAbilities():
    return [*AbilityFactory.GiveKeywordToInPlayWhenApplyThis(Ally,control_by="You",health=1)]
