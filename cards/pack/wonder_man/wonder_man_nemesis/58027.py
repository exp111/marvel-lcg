from . import *

# Brother vs. Brother

def GetAbilities() -> Sequence['Ability']:

    def additional_cost(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        player = message.attacker.GetControlByPlayer()
        if not CostFunc.Discard("YourHandCards").PayCost(effect, player):
            message.SetBeInstead(effect)

    return [
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.NonKeyword,
            Friend,
            additional_cost,
            attack_targets=CardFinder(name="Grim Reaper"),
        ),
    ]

