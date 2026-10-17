from . import *

# Hulk
def GetAbilities():
    return [
        AbilityFactory.ThisGainKeyword(lambda effect,ui: effect.this.CastTo(Ally).GetCounters("rage"),
            attack=1,change_on_event=OnEvent.Counter("This","rage")),
        AbilityFactory.AfterUnitAttackEnd(AbilityType.Response,Villain,
            lambda effect,message: Faces.PlaceCountersOn([effect.this],1,"rage",effect),against_who="You"),
    ]
