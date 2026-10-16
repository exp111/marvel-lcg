from . import *

# Spider-Woman
def GetAbilities():
    def spider_woman(effect,message):
        this=effect.this.CastTo(Ally)
        Faces.PlaceCountersOn([this],1,"limb",effect,maximum=8)
        amount=this.GetCounters("limb")
        effect.GetInitiator().MayChooseOneAbility(effect,
            AbilityFactory.ForChoiceAbility("Discard Spider-Woman to deal damage equal to her limb counters",
                lambda targets: this.DealDamage(targets,amount,effect))
            .SetCostFunc(CostFunc.Discard("This")).SetTarget(Enemy))
    return [AbilityFactory.AfterUnitThwartEnd(AbilityType.Response,Friend,spider_woman,
        conditions=[lambda effect,message: message.trigger.GetControlBy()==effect.GetInitiator()])]
