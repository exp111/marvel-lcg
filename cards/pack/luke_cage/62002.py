from . import *

# Jessica Jones
def GetAbilities():
    return [AbilityFactory.ThisGainKeyword(
        lambda effect,ui: min(4,effect.GetInitiator().GetIdentity().tough),
        thwart=1,change_on_event=OnEvent.Status("YourIdentity","Tough"))]
