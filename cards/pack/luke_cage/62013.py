from . import *

# Misty Knight
def GetAbilities():
    return [AbilityFactory.ThisGainKeyword(lambda effect,ui: int(effect.this.CastTo(Ally).tough>0),
        attack=2,thwart=2,change_on_event=OnEvent.Status("This","Tough"))]
