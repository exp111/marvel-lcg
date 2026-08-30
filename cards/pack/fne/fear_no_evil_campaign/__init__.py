from cards.pack import *


def CampaignEnvironmentSetup(
    operation: Callable[['Effect'], None],
) -> 'Ability':
    def setup(
        effect: 'Effect',
        message: 'Message.WhenCardEnterPlay',
    ) -> None:
        Unused(message)
        operation(effect)

    return AbilityFactory.WhenCardEnterPlay(
        AbilityType.Campaign,
        "This",
        setup,
    ).SetName("Resolve this campaign environment's Setup ability")


def SearchRewardAfterMulligans(
    card_type: Type['TC'],
    card_type_name: str,
) -> 'Ability':
    def search(effect: 'Effect') -> None:
        for player in Worlds.GetPlayers(effect):
            face = Search.PlayerCard(
                effect,
                player,
                include_player_deck=True,
                include_discard_pile=True,
                may=True,
                card_type=card_type,
            )
            if not face:
                continue
            player.GainCard(face, effect)
            if Worlds.IsExpert(effect) and player.hand_cards.Get():
                player.AskDiscardFace(player.hand_cards.Get(), effect)

    article = "an" if card_type_name[:1].lower() in "aeiou" else "a"
    return CampaignEnvironmentSetup(search).SetName(
        f"After mulligans, search for {article} {card_type_name}"
    )


def FlipAfterYouReveal(which_card: Type['CardFace']) -> 'Ability':
    def flip(
        effect: 'Effect',
        message: 'Message.AfterCardRevealedEnd',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(Ally)
        this.HealHealth("All", effect)
        this.card.Flip(effect)

    return AbilityFactory.AfterPlayerRevealCard(
        AbilityType.ForcedResponse,
        "You",
        which_card,
        flip,
    )
