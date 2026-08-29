from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        public_support = Search.SearchForCard(
            effect,
            message.GetToPlayer(),
            include_set_aside=True,
            name="Public Support",
            card_type=Environment,
        )
        if public_support:
            public_support.FlipTo(effect, face_up=True)
            public_support.PutIntoPlay(message.GetToPlayer(), effect)

    def call_in_minion(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        Unused(message)
        player = effect.GetInitiator()
        deck = Worlds.GetEncounterDeck(effect)
        deck.ShuffleWithDiscardPile(False, effect)
        minion = Worlds.DiscardEncounterCardsUntil(effect, card_type=Minion)
        if minion:
            minion.Reveal(player, effect)

    def make_action(*, expert: bool, threat: int) -> 'Ability':
        return AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            call_in_minion,
            conditions=[
                lambda effect, message:
                    Worlds.IsExpert(effect) == expert,
                lambda effect, message:
                    effect.this.CastTo(MainScheme).threat >= threat,
            ],
        ).SetCostFunc(CostFunc.RemoveThreatFrom(
            "This",
            threat,
        )).SetName(
            f"Remove {threat} threat, reshuffle the encounter discard pile, and reveal a minion"
        ).AnyPlayerCanDoThis()

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        make_action(expert=False, threat=5),
        make_action(expert=True, threat=4),
        AbilityFactory.IfThisSchemeStageIsCompletedPlayersLoseTheGame(),
    ]
