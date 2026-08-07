from . import *

# Teamwork

def GetAbilities() -> Sequence['Ability']:

    def teamwork(effect: 'Effect', message: 'Message.WhenUnitUseBasicPower') -> None:
        this = effect.this.CastTo(Event)
        Unused(this)

        allies = effect.cost_func.Get(CostFunc.Exhaust).return_exhausted_cards
        allies = Filter.ByType(allies, Ally)

        message.AddThatMatchingPower(allies, effect)


    return [
        AbilityFactory.WhenUnitUseBasicPower(
            AbilityType.HeroInterrupt,
            "You",
            teamwork,
            powers=["THW", "ATK"]
        ).SetPlay().SetLabel()
        .SetCostFunc(CostFunc.Exhaust("YourAlly")),
    ]
