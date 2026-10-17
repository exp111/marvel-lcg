from . import *

# Luke Cage
from .helpers import UnbreakableSkin

def GetAbilities():
    def bulletproof(effect,message):
        effect.this.DealDamage([message.trigger],DamageProperty(1,ignore_tough=True,unpreventable=True),effect)
    return [*UnbreakableSkin(),AbilityFactory.AfterStatusDiscardFrom(
        AbilityType.ForcedResponse,"This","Tough",bulletproof)]
