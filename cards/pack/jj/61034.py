from . import *

# Innate Aggression
def GetAbilities():
    return [*AbilityFactory.GiveKeywordToInPlayWhenApplyThis(Hero,control_by="You",attack=1)]
