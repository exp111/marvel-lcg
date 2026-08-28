from cards.pack.fne import *


PHOTOGRAPHIC_REFLEXES_IDS = ["60040a", "60040b", "60040c"]
ASPECT_OR_BASIC_EVENT = CardFinder(
    card_type=Event,
    card_classes=["Aspect", "Basic"],
)


class BuffDaredevilEventDiscount(Buff):
    def __init__(self) -> None:
        super().__init__()
        self.discount = 0

    def Add(self) -> None:
        self.discount += 1
        self.SetUIText(str(self.discount))

    def Consume(self) -> None:
        self.discount = 0
        self.SetUIText("")

    @override
    def OnRoundEnd(self) -> None:
        super().OnRoundEnd()
        self.Consume()

    def __bool__(self) -> bool:
        return self.discount > 0


def RegisterPhotographicReflexesPlayAbilities(face: 'CardFace') -> None:
    if not ASPECT_OR_BASIC_EVENT.Check(face):
        return

    play_effects = [
        effect for effect in face.effect.GetAll()
        if effect.ability.is_play
    ]

    for play_effect in play_effects:
        already_registered = any(
            getattr(
                effect.ability,
                "photographic_reflexes_play_effect",
                None,
            ) is play_effect
            for effect in face.effect.given_effects
        )
        if already_registered:
            continue

        def is_tucked_under_echo_in_hero_form(
            effect: 'Effect',
            message: 'Message2',
        ) -> bool:
            player = effect.GetInitiator()
            return (
                player.IsHero() and
                effect.this.card.area ==
                player.GetIdentity().GetPlacedCardArea()
            )

        def can_discard_for_this_play(
            effect: 'Effect',
            reflexes: 'CardFace',
            play_effect: 'Effect'=play_effect,
        ) -> bool:
            if not effect.bind_message:
                return False
            return effect.GetInitiator().CanPlayEffectLikeInHand(
                play_effect,
                effect.bind_message,
                update_resources_cost=-2,
                excluded_payment_faces=[reflexes],
            )

        def play_with_photographic_reflexes(
            effect: 'Effect',
            message: 'Message2',
            play_effect: 'Effect'=play_effect,
        ) -> None:
            effect.GetInitiator().PlayEffectLikeInHand(
                play_effect,
                message,
                update_resources_cost=-2,
            )

        proxy = Ability(
            play_effect.ability.type,
            play_effect.ability.when,
            [is_tucked_under_echo_in_hero_form],
            play_with_photographic_reflexes,
        ).SetName(play_effect.ability.name)
        proxy.SetCostFunc(CostFunc.Discard(
            Select.From(
                "YourHandCards",
                finder=CardFinder(
                    card_ids=PHOTOGRAPHIC_REFLEXES_IDS,
                    check_effect_fn=can_discard_for_this_play,
                ),
            )
        )).NoOutOfPlayLimit()
        proxy.photographic_reflexes_play_effect = play_effect
        face.effect.RegisterGiven(proxy)


def DaredevilEventDiscountAbilities() -> List['Ability']:
    def get_buff(effect: 'Effect') -> BuffDaredevilEventDiscount:
        return effect.GetInitiator().GetIdentity().GetBuff(
            BuffDaredevilEventDiscount
        )

    def consume_discount(
        effect: 'Effect',
        message: 'Message.AfterPlayerPlayedCard',
    ) -> None:
        get_buff(effect).Consume()

    return [
        AbilityFactory.ReduceCostToPlayFaceWhen(
            Event,
            lambda effect: get_buff(effect).discount,
            "You",
            conditions=[
                lambda effect, message: bool(get_buff(effect)),
            ],
        ),
        AbilityFactory.AfterPlayerPlayedCard(
            AbilityType.NonKeyword,
            "You",
            Event,
            consume_discount,
            conditions=[
                lambda effect, message: bool(get_buff(effect)),
            ],
        ),
    ]
