from . import *

# 4K Digital Camcorder
from .helpers import Alias

def GetAbilities():
    def affordable(effect, face):
        alias=Alias(effect)
        return alias is not None and alias.GetCounters("evidence") >= max(0, face.CastTo(Minion).health-2)
    def pay_evidence(targets, effect):
        alias=Alias(effect)
        for minion in effect.targets:
            cost=max(0, minion.CastTo(Minion).health-2)
            if not alias or (cost and not alias.RemoveCountersInternal(cost,"evidence",effect,forced=False)):
                return False
        return True
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.AlterEgoAction,
        lambda effect,message: Faces.DiscardAll(effect.targets,effect))
        .SetCostFunc(CostFunc.Exhaust("This"))
        .SetCostFunc(CostFunc.Custom(Select.From("This"),pay_evidence))
        .SetTarget(Minion,non_trait="ELITE",canbe_discard=True,check_fn=affordable)]
