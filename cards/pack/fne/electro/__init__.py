from cards.pack import *


ELECTRO = CardFinder(name="Electro", card_type=Villain)
ELECTRIC_CHARGE = CardFinder(name="Electric Charge", card_type=Attachment)


def GetElectricCharge(effect: 'Effect') -> 'Attachment|None':
    face = Worlds.FindCardOnField(effect, name="Electric Charge", card_type=Attachment)
    return face if Attachment.IsType(face) else None


def ElectroVillainAbilities(
    reveal_charges: int,
    scheme_charges: int,
    *,
    attach_charge: bool=True,
) -> List['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        Unused(message)
        if attach_charge:
            this = effect.this.CastTo(EncounterVillain)
            SetupCards.AttachTo(
                effect,
                attach_to=this,
                name="Electric Charge",
                card_type=Attachment,
            )
        charge = GetElectricCharge(effect)
        if charge:
            Faces.PlaceCountersOn([charge], f"{reveal_charges}*", 'charge', effect)

    def after_scheme(effect: 'Effect', message: 'Message.AfterUnitSchemeEnd') -> None:
        Unused(message)
        charge = GetElectricCharge(effect)
        if charge:
            Faces.PlaceCountersOn([charge], scheme_charges, 'charge', effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.AfterUnitSchemeEnd(
            AbilityType.ForcedResponse,
            "This",
            after_scheme,
        ),
    ]
