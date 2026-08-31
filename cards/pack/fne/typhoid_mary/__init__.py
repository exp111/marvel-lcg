from cards.pack import *


TYPHOID_SET = CardFinder(set_name="Typhoid Mary")
TYPHOID_VILLAIN = CardFinder(set_name="Typhoid Mary", card_type=Villain)
DISTURBED_PSYCHE = CardFinder(name="Disturbed Psyche", card_type=Environment)


def GetTyphoidVillain(effect: 'Effect') -> 'Villain|None':
    face = Worlds.FindCardOnField(effect, TYPHOID_VILLAIN)
    return face if Villain.IsType(face) else None


def RevealEstablishTrust(effect: 'Effect') -> None:
    mary = Worlds.FindCardOnField(effect, name="Mary Walker", card_type=Attachment)
    if mary:
        mary.card.Flip(effect)


def TyphoidVillainAbilities(maximum_hp: int, *, damage_each_identity: bool=False) -> List['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        if damage_each_identity:
            effect.this.DealDamage(Worlds.GetPlayersIdentities(effect), 1, effect)

    def would_be_defeated(effect: 'Effect', message: 'Message.WhenUnitWouldBeDefeated') -> None:
        villain = effect.this.CastTo(Villain)
        message.SetBeInstead(effect)
        psyche = Worlds.FindCardOnField(effect, DISTURBED_PSYCHE)
        if psyche:
            Faces.PlaceCountersOn([psyche], 1, 'damage', effect)
        villain.ResetHealth(effect)

    abilities: List[Ability] = [
        AbilityFactory.WhenUnitWouldBeDefeated(
            AbilityType.ForcedInterrupt,
            "This",
            would_be_defeated,
        ),
    ]
    if damage_each_identity:
        abilities.insert(0, AbilityFactory.WhenThisRevealed(None, revealed))
    return abilities


def IsTyphoidMary(face: 'CardFace') -> bool:
    return face.name == "Typhoid Mary"


def IsBloodyMary(face: 'CardFace') -> bool:
    return face.name == "Bloody Mary"
