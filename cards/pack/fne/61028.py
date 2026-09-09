
from . import *

# * Second Chance

def GetAbilities() -> Sequence['Ability']:

    def second_chance(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        this = effect.this.CastTo(PlayerSideScheme)
        Unused(this)

        def shuffle_for_player(player: 'Player') -> None:
            faces = [
                face for face in player.discard_pile.Get()
                if ClassCard.IsType(face) and face.IsClass("IdentitySpecific")
            ]
            if not faces:
                return

            if player.MayChooseOneText(["Shuffle all identity-specific cards from your discard pile into your deck"]):
                Faces.MoveAllTo(faces, player.player_deck, effect)
                player.player_deck.Shuffle(effect)

        Players.ForEachPlayer(effect, shuffle_for_player)

    return [
        AbilityFactory.WhenSchemeBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            second_chance,
        ),
    ]
