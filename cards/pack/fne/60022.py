from . import *

# * Ghost Rider


def GetAbilities() -> Sequence['Ability']:

    def confuse_attacked_enemy(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        Faces.GiveStatus(message.attacked_targets, "Confused", effect)

    return [
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.Interrupt,
            "This",
            confuse_attacked_enemy,
            attack_targets=Minion,
        ).SetCost(Cost("Y")),
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.Interrupt,
            "This",
            confuse_attacked_enemy,
            attack_targets=Villain,
        ).SetCost(Cost("YY")),
    ]
