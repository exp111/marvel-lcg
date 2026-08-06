from . import *

# * Signature Sunglasses

def GetAbilities() -> Sequence['Ability']:

    def can_use_signature_sunglasses(effect: 'Effect', message: 'Message.AfterUnitChangeForm') -> bool:
        ionic = FindIonicPhysiology(effect)
        if not ionic:
            return False
        if ionic.GetPlacedCardArea().GetSize() > 0:
            return True
        if ionic.GetPlacedCardArea().GetSize() >= 3:
            return False
        return any(
            (Event.IsType(face) or Resource.IsType(face)) and HasPrintedEnergy(face)
            for face in effect.GetInitiator().discard_pile.Get(True)
        )

    def signature_sunglasses(effect: 'Effect', message: 'Message.AfterUnitChangeForm') -> None:
        initiator = effect.GetInitiator()
        ionic = FindIonicPhysiology(effect)
        if not ionic:
            return

        tuck_ability = None
        if ionic.GetPlacedCardArea().GetSize() < 3:
            tuck_ability = AbilityFactory.ForChoiceAbility(
                "Tuck an event or resource with a printed energy resource",
                lambda targets: ionic.TuckCardUnderHere(targets, effect),
            ).SetTarget(
                Event|Resource,
                from_where=["YourDiscardPile"],
                check_fn=lambda effect, face: HasPrintedEnergy(face),
            )

        return_ability = None
        if ionic.GetPlacedCardArea().GetSize() > 0:
            return_ability = AbilityFactory.ForChoiceAbility(
                "Add a card tucked under Ionic Physiology to your hand",
                lambda targets: Faces.ReturnToHand(targets, initiator, effect),
            ).SetTarget(ionic.GetPlacedCardArea().GetAll())

        initiator.ChooseAbilities(effect, tuck_ability, return_ability)

    return [
        AbilityFactory.AfterUnitChangeForm(
            AbilityType.Response,
            "YourIdentity",
            signature_sunglasses,
            conditions=[can_use_signature_sunglasses],
        ),
    ]

