from . import *


def GetAbilities() -> Sequence['Ability']:
    def study_the_tape(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        player = effect.GetInitiator()
        finder = ASPECT_OR_BASIC_EVENT | CardFinder(
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
