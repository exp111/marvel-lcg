from . import *


def GetAbilities() -> Sequence['Ability']:
    def gain_ranged(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldAttack',
    ) -> None:
        message.GainRanged(effect)

    def replace_damage(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldTakeDamage',
    ) -> None:
        scheme = GetGetawayScheme(effect)
        if not scheme:
            return
        damage = message.PreventDamage("All", effect)
        scheme.RemoveThreatFromSchemes(
            [scheme],
            damage,
            effect,
            ignore_crisis=True,
        )

    def flip_when_clear(
        effect: 'Effect',
        message: 'Message.AfterSchemeRemoveThreat',
    ) -> None:
        Unused(message)
        if effect.this.card.face == effect.this:
            effect.this.card.Flip(effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(Villain),
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.NonKeyword,
            "AttachedCharacter",
            gain_ranged,
        ),
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            "AttachedCharacter",
            replace_damage,
        ),
        AbilityFactory.AfterSchemeRemoveThreat(
            AbilityType.NonKeyword,
            GETAWAY_SCHEME,
            flip_when_clear,
            last_threat=True,
        ),
    ]
