from . import *

# Super-Charged

def GetAbilities() -> Sequence['Ability']:

    def super_charged(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        this = effect.this.CastTo(Upgrade)
        Unused(this)

        initiator = effect.GetInitiator()
        faces = effect.cost_func.Get(CostFunc.Discard).return_discarded_cards
        size = FacesCounter.GetPrintedResourcesIcon(faces, initiator.hand_cards)
        Faces.PlaceCountersOn([this], size, 'charge', effect)

    def super_charged_interrupt(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        this = effect.this.CastTo(Upgrade)

        discard_cost = effect.cost_func.Get(CostFunc.Discard)
        charge_counters = discard_cost.return_discarded_counters.get(this, {}).get('charge', 0)
        value = min(8, charge_counters * 2)
        message.GainATKForThisAttack(value, effect)


    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            super_charged
        ).SetCostFunc(CostFunc.Discard(
            "YourHandCards",
            card_type=Resource,
        )),
        AbilityFactory.WhenUnitMakeAttack(
            AbilityType.HeroInterrupt,
            "You",
            super_charged_interrupt,
            is_basic_attack=True,
            conditions=[
                lambda effect, message:
                    effect.this.CastTo(Upgrade).GetCounters('charge') > 0
            ]
        ).SetCostFunc(CostFunc.Discard("This")),
    ]
