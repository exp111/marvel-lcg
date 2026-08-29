from . import *


def GetAbilities() -> Sequence['Ability']:
    discount = AbilityFactory.UpdateCostOfCardInternal(
        Upgrade,
        -1,
        "AnyPlayer",
        is_play=True,
        conditions=[
            lambda effect, message: message.GetToPlayer() == GetSchemeOwner(effect),
        ],
    ).LimitOncePerRound()

    def entered(effect: 'Effect', message: 'Message.AfterCardEnterPlay') -> None:
        PlaceThreatHere(effect, 1)

    return [
        discount,
        AbilityFactory.AfterCardEnterPlay(
            AbilityType.ForcedResponse,
            CardFinder(card_type=Attachment) | CardFinder(card_type=Upgrade),
            entered,
            conditions=[
                lambda effect, message: IsInThisPlayArea(message.trigger, effect),
            ],
        ),
        *ProtectionRacketLossAbilities(),
    ]
