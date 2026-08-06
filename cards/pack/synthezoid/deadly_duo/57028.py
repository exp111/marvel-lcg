from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        faces = player.DiscardDeckTopCards(3, effect)
        effect.this.PlaceThreatOnSchemes(
            "MainScheme", FacesCounter.GetDifferentTypesCount(faces), effect
        )

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
