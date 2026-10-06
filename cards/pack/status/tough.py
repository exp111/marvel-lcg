from . import *

# Tough

def GetAbilities() -> Sequence['Ability']:

    def set_be_instead(effect: 'Effect', message: 'Message.WhenUnitWouldTakeDamage'):
        this = effect.this.CastTo(StatusCard)
        message.PreventDamage(message.be_dealt_damage, effect)
        message.SetBeInstead(effect)
        unit = this.GetBindFace()
        unit.DiscardTough(effect, rule=1)

    return [
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.Status,
            "AttachedCharacter",
            set_be_instead,
            conditions=[
                lambda effect, message:
                    not message.property.ignore_tough
            ]
        )
    ]

