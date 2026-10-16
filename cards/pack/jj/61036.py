from . import *

# Innate Perception
def GetAbilities():
    return [*AbilityFactory.GiveKeywordToInPlayWhenApplyThis(Hero,control_by="You",thwart=1)]
