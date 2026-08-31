from . import *


def GetAbilities() -> Sequence['Ability']:
    def cancel_boost(
        effect: 'Effect',
        message: 'Message.WhenCardWouldMoveToArea',
    ) -> None:
        message.SetCannot(effect)
        Faces.RemoveCountersOn([effect.this], 1, "support", effect)

    cancel = AbilityFactory.WhenCardWouldMoveToArea(
        AbilityType.Interrupt,
        CardFace,
        cancel_boost,
        conditions=[
            lambda effect, message:
                message.into_area.flags.is_attach_boost_area,
            lambda effect, message:
                bool(
                    message.into_area.bind_card and
                    Enemy.IsType(message.into_area.bind_card.face)
                ),
            lambda effect, message:
                effect.this.GetCounters("support") > 0,
        ],
    ).AnyPlayerCanDoThis().SetName(
        "Remove 1 support counter instead of giving this boost card"
    )

    return [
        cancel,
        PublicSupportAfterMinionDefeated(),
    ]
