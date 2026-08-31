from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        if Worlds.IsExpert(effect):
            effect.this.PlaceThreatOnSchemes([effect.this], "3*", effect)

    def defeated(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        psyche = Worlds.FindCardOnField(effect, DISTURBED_PSYCHE)
        if psyche:
            Faces.PlaceCountersOn([psyche], 1, 'threat', effect)
        this.card.Flip(effect, call_reveal=False)
        mary = this.card.face
        villain = GetTyphoidVillain(effect)
        if villain and Attachment.IsType(mary):
            mary.AttachTo2(villain, effect)

    return [
        AbilityFactory.WhenCardSetup("This", setup),
        AbilityFactory.WhenThisRevealed(
            None,
            lambda effect, message:
                effect.this.PlaceThreatOnSchemes([effect.this], "3*", effect)
                if Worlds.IsExpert(effect) else None,
        ),
        AbilityFactory.WhenSchemeBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            defeated,
        ),
    ]
