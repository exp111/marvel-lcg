from . import *

# Alias Investigations
def GetAbilities():
    def investigate(effect,message):
        this=effect.this.CastTo(Support)
        Faces.PlaceCountersOn([this],2,"evidence",effect)
        villain=Worlds.ChooseVillain(effect, CardFinder(card_type=Villain,
            check_face_fn=lambda face: 0 < face.health <= this.GetCounters("evidence")))
        if villain:
            if effect.GetInitiator().MayChooseOneText(["Spend evidence equal to the villain's remaining hit points to defeat this stage"]):
                if this.RemoveCountersInternal(villain.health,"evidence",effect,forced=False):
                    Faces.DefeatUnits([villain],this,effect)
    return [AbilityFactory.AfterSchemeBeDefeated(AbilityType.Response,SchemeSide2,investigate)
        .SetCostFunc(CostFunc.Exhaust("This"))]
