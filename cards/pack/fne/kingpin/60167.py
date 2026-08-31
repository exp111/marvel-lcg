from . import *


def GetAbilities() -> Sequence['Ability']:
    def store_damage(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldTakeDamage',
    ) -> None:
        damage = message.will_take_damage
        message.SetBeInstead(effect)
        Faces.PlaceCountersOn([effect.this], damage, "damage", effect)
        if effect.this.GetCounters("damage") >= 8:
            Faces.DiscardAll([effect.this], effect)

    return [
        *AttachToKingpinOrSurge(retaliate=1),
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            "AttachedCharacter",
            store_damage,
        ),
    ]
