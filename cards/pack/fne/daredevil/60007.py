from . import *


def GetAbilities() -> Sequence['Ability']:

    def redirect_consequential_damage(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldTakeDamage',
    ) -> None:
        message.SetBeInstead(effect)
        daredevil = effect.GetInitiator().GetIdentity()
        daredevil.TakeDamage(
            message.source,
            message.will_take_damage,
            effect,
            message.would_deal_damage_message.would_attack_unit_message,
        )

    return [
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            "This",
            redirect_consequential_damage,
            is_consequential_damage=True,
            conditions=[
                lambda effect, message: effect.GetInitiator().IsHero(),
            ],
        ),
    ]
