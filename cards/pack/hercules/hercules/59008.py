from . import *


def GetAbilities() -> Sequence['Ability']:

    def redirect_attack(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        message.ReplaceTarget(effect.this.CastTo(Ally))
        message.Present_Activate(None, effect)

    def attacks_your_identity(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> bool:
        identity = effect.this.GetControlByPlayer().GetIdentity()
        return message.HasTarget(identity)

    def draw_card(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        effect.GetInitiator().DrawUp(1, effect)

    return [
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.ForcedInterrupt,
            Minion,
            redirect_attack,
            conditions=[attacks_your_identity],
        ),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            draw_card,
        ).SetCostFunc(CostFunc.Exhaust("This")),
    ]
