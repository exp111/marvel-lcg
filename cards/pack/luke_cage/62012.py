from . import *

# Iron Fist
def GetAbilities():
    def iron_fist(effect,message):
        amount=effect.this.CastTo(Ally).attack
        if amount>0: message.PreventDamage(amount,effect)
    return [AbilityFactory.WhenUnitWouldTakeDamage(AbilityType.Interrupt,"This",iron_fist,
        is_from_attack=True,while_defending=True,who_deal_damage=Enemy)]
