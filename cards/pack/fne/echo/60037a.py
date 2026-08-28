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

    def play_tucked_event_with_photographic_reflexes(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        player = effect.GetInitiator()
        player.PlayOneCardLikeInTurn(
            ASPECT_OR_BASIC_EVENT.Checks(
                player.GetIdentity().GetPlacedCardArea().GetAll()
            ),
            effect,
            update_resources_cost=-2,
            forced=True,
        )

    def has_tucked_event(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> bool:
        return bool(
            ASPECT_OR_BASIC_EVENT.Checks(
                effect.this.GetPlacedCardArea().GetAll()
            )
        )

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
            AbilityType.HeroAction,
            play_tucked_event_with_photographic_reflexes,
            conditions=[
                has_tucked_event,
            ],
        ).SetName("Photographic Reflexes")
        .SetCostFunc(CostFunc.Discard(
            Select.From(
                "YourHandCards",
                finder=CardFinder(card_ids=PHOTOGRAPHIC_REFLEXES_IDS),
            )
        )),
        *DaredevilEventDiscountAbilities(),
    ]
