from . import *

# Echo
def GetAbilities():
    def reduce(effect,message):
        identity=effect.GetInitiator().GetIdentity()
        if Hero.IsType(identity): message.ReduceDamage(identity.CastTo(Hero).defense,effect)
    return [AbilityFactory.WhenUnitWouldTakeDamage(AbilityType.NonKeyword,"This",reduce,
        is_from_attack=True,who_deal_damage=Enemy)]
