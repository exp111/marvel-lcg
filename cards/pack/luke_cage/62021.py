from . import *

# She-Hulk
def GetAbilities():
    return [AbilityFactory.AfterCardEnterPlay(AbilityType.Response,"This",
        lambda effect,message: Faces.GiveStatus(effect.targets,"Tough",effect))
        .SetTarget("YourIdentity",canbe_tough=True)]
