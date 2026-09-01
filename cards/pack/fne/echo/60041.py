from . import *


def GetAbilities() -> Sequence['Ability']:
    def study_the_tape(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        player = effect.GetInitiator()
        # CardFinder.__or__ mutates its left operand.  Build this expanded
        # finder from a fresh base so Study the Tape cannot permanently add
        # Photographic Reflexes to the shared finder used by Choreography.
        finder = AspectOrBasicEventFinder() | CardFinder(
            card_ids=PHOTOGRAPHIC_REFLEXES_IDS,
        )
        face = Search.PlayerCard(
            effect,
            player,
            include_player_deck=False,
            include_discard_pile="All",
            finder=finder,
        )
        if face:
            player.GainCard(face, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            study_the_tape,
        ).SetPlay().SetLabel(),
    ]
