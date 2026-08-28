from . import *


def GetAbilities() -> Sequence['Ability']:
    def watch_and_learn(
        effect: 'Effect',
        message: 'Message.AfterPlayerPlayedCard',
    ) -> None:
        this = effect.this.CastTo(Hero)
        if not this.TuckCardUnderHere(message.played_face, effect):
            return

        tucked = this.GetPlacedCardArea().GetAll()
        overflow = len(tucked) - 3
        if overflow > 0:
            effect.GetInitiator().AskDiscardFaces(
                tucked,
                (overflow, overflow),
                effect,
            )

    def discard_photographic_reflexes(
        effect: 'Effect',
        message: 'Message.WhenPlayerWouldPlayCard',
    ) -> None:
        player = effect.GetInitiator()
        player.AskDiscardFaces(
            GetPhotographicReflexesInHand(player),
            (1, 1),
            effect,
        )

    def tucked_event(effect: 'Effect', face: 'CardFace') -> bool:
        return face.card.area == effect.this.GetPlacedCardArea()

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
        *AbilityFactory.YouMayPlayCardLikeInHand(
            AbilityType.NonKeyword,
            ASPECT_OR_BASIC_EVENT,
            from_where="ThisPlacedCard",
            conditions=[
                lambda effect, message:
                    effect.GetInitiator().IsHero() and
                    HasPhotographicReflexesInHand(effect),
            ],
        ),
        AbilityFactory.ReduceCostToPlayFaceWhen(
            ASPECT_OR_BASIC_EVENT,
            2,
            "You",
            conditions=[
                lambda effect, message:
                    tucked_event(effect, message.check_effect.this) and
                    HasPhotographicReflexesInHand(effect),
            ],
        ),
        AbilityFactory.WhenPlayerWouldPlayCard(
            AbilityType.ForcedInterrupt,
            "You",
            ASPECT_OR_BASIC_EVENT,
            discard_photographic_reflexes,
            conditions=[
                lambda effect, message:
                    message.from_area == effect.this.GetPlacedCardArea(),
            ],
        ),
        *DaredevilEventDiscountAbilities(),
    ]
