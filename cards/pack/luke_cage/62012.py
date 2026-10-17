from . import *

# Iron Fist
def GetAbilities():
    def iron_fist(effect,message):
        amount=effect.this.CastTo(Ally).attack
        # Establish prevention when he defends, before boosts and tough resolve.
        effect.this.effect.RegisterTemp(
            AbilityFactory.WhenUnitWouldTakeDamage(AbilityType.Temp0,None,
                lambda temp,damage: damage.PreventDamage(amount,effect),
                is_from_attack=message.would_atk_message),
            unregister_after_exec=True,until_event_end=message.would_atk_message)
    return [AbilityFactory.WhenUnitDefendAgainstAttack(AbilityType.Interrupt,"This",iron_fist,
        against_who=Enemy)]
