from . import *

# Wonder Fans

def GetAbilities() -> Sequence['Ability']:

    def wonder_fans(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        initiator = effect.GetInitiator()
        ionic = FindIonicPhysiology(effect)

        tuck_ability = None
        if ionic and ionic.GetPlacedCardArea().GetSize() < 3:
            tuck_ability = AbilityFactory.ForChoiceAbility(
                "Tuck an event with a printed energy resource under Ionic Physiology",
                lambda targets: ionic.TuckCardUnderHere(targets, effect),
            ).SetTarget(
                Event,
                from_where=["YourDiscardPile"],
                check_fn=lambda effect, face: HasPrintedEnergy(face),
            )

        initiator.ChooseAbilities(
            effect,
            tuck_ability,
            AbilityFactory.ForChoiceAbility(
                "Draw 1 card",
                lambda targets: initiator.DrawUp(1, effect),
            ),
        )

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.AlterEgoAction,
            wonder_fans,
        ).SetCostFunc(CostFunc.Exhaust("This")),
    ]

