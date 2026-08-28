from . import *


def GetAbilities() -> Sequence['Ability']:
    def watch_and_learn(
        effect: 'Effect',
        message: 'Message.AfterPlayerPlayedCard',
    ) -> None:
        this = effect.this.CastTo(Hero)
        if not this.TuckCardUnderHere(message.played_face, effect):
            return

        RegisterPhotographicReflexesPlayAbilities(message.played_face)
        tucked = this.GetPlacedCardArea().GetAll()
        overflow = len(tucked) - 3
        if overflow > 0:
            effect.GetInitiator().AskDiscardFaces(
                tucked,
                (overflow, overflow),
                effect,
            )

    def sync_photographic_reflexes_play_abilities(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        for face in effect.this.GetPlacedCardArea().GetAll():
            RegisterPhotographicReflexesPlayAbilities(face)

    return [
        AbilityFactory.AfterPlayerPlayedCard(
            AbilityType.Response,
            "AnyPlayer",
            ASPECT_OR_BASIC_EVENT,
            watch_and_learn,
            conditions=[
                lambda effect, message:
                    message.from_area != effect.this.GetPlacedCardArea(),
                lambda effect, message:
                    message.played_face.card.area ==
                    message.GetToPlayer().discard_pile,
            ],
        ),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.NonKeyword,
            sync_photographic_reflexes_play_abilities,
        ),
        *DaredevilEventDiscountAbilities(),
    ]
