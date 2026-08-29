from . import *


def GetAbilities() -> Sequence['Ability']:
    def betty_brant(
        effect: 'Effect',
        message: 'Message.WhenBoostCardTurnedFaceUp',
    ) -> None:
        message.CancelAllBoostIcons(effect)
        message.CancelBoostAbility(effect)
        activating_enemy = message.would_message.trigger.CastTo(Enemy)
        activating_enemy.GiveFacedownBoostCardsInternal(
            1,
            effect,
            message.would_message,
        )

    ability = AbilityFactory.WhenBoostCardTurnedFaceUp(
        AbilityType.Interrupt,
        None,
        betty_brant,
    )
    for cost in StaminaCost():
        ability.SetCostFunc(cost)
    return [ability]
