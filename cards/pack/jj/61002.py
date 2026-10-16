from . import *

# Alias Investigations
def GetAbilities():
    def investigate(effect,message):
        this=effect.this.CastTo(Support)
        Faces.PlaceCountersOn([this],2,"evidence",effect)
        villain=Worlds.FindVillain(effect)
        if villain and villain.health>0 and this.GetCounters("evidence")>=villain.health:
            if effect.GetInitiator().MayChooseOneText(["Spend evidence equal to the villain's remaining hit points to defeat this stage"]):
                if this.RemoveCountersInternal(villain.health,"evidence",effect,forced=False):
                    Faces.DefeatUnits([villain],this,effect)
    return [AbilityFactory.AfterSchemeBeDefeated(AbilityType.Response,SchemeSide2,investigate)
        .SetCostFunc(CostFunc.Exhaust("This"))]
