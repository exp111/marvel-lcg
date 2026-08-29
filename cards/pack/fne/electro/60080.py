from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        Faces.ExhaustAll(player.GetControlUpgrade(), effect)

    def would_ready(effect: 'Effect', message: 'Message.WhenCardWouldReady') -> None:
        this = effect.this.CastTo(Attachment)
        player = message.trigger.GetControlByPlayer()
        if not player:
            message.SetBeInstead(effect)
            return

        def pay(targets: Sequence['CardFace']) -> None:
            Faces.RemoveCountersOn([this], 1, 'drain', effect)

        def remain_exhausted(targets: Sequence['CardFace']) -> None:
            message.SetBeInstead(effect)

        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbilityWithCost(
                Cost("Y", or_cost=Cost("2")),
                "Spend an energy resource or 2 resources of any type → remove 1 drain counter",
                pay,
            ),
            AbilityFactory.ForChoiceAbility(
                "Do not pay (this card does not ready)",
                remain_exhausted,
            ),
        )

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay("YourIdentity"),
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardWouldReady(
            AbilityType.ForcedInterrupt,
            Upgrade,
            would_ready,
            control_by="AttachedPlayer",
        ),
    ]
