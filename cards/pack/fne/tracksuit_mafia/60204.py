from . import *


def GetAbilities() -> Sequence['Ability']:
    def tracksuit_mafia_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(EncounterSideScheme)
        minion = Worlds.DiscardEncounterCardsUntil(
            effect,
            trait="TRACKSUIT",
            card_type=Minion,
        )
        if minion:
            this.TuckCardUnderHere(minion, effect)

    def reveal_tucked_minion(
        effect: 'Effect',
        message: 'Message.AfterCardRevealedEnd',
    ) -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        tucked = TRACKSUIT_MINION.Checks(this.GetPlacedCardArea().GetAll())
        if not tucked:
            return
        player = message.GetToPlayer()
        minion = player.AskChooseFace(
            tucked,
            effect,
            prompt="Choose a tucked TRACKSUIT minion to reveal",
            forced=True,
        )
        if minion:
            minion.Reveal(player, effect)

    return [
        AbilityFactory.WhenThisRevealed(None, tracksuit_mafia_revealed),
        AbilityFactory.AfterPlayerRevealCard(
            AbilityType.ForcedResponse,
            "AnyPlayer",
            TRACKSUIT_MINION,
            reveal_tucked_minion,
            conditions=[
                lambda effect, message:
                    message.reveal_message.IsFromEncounterDeck(),
            ],
        ),
    ]
