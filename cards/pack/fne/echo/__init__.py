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


def GetPhotographicReflexesInHand(player: 'Player') -> List['CardFace']:
    return CardFinder(card_ids=PHOTOGRAPHIC_REFLEXES_IDS).Checks(
        player.hand_cards.GetAll()
    )


def HasPhotographicReflexesInHand(effect: 'Effect') -> bool:
    return bool(GetPhotographicReflexesInHand(effect.GetInitiator()))


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
