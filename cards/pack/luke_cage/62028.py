from . import *

# Internal Injury
def GetAbilities():
    return [
        AbilityFactory.AfterPhaseEnd(AbilityType.ForcedResponse,"Player",lambda effect,message:
            effect.this.DealDamage([effect.GetInitiator().GetIdentity()],DamageProperty(3,ignore_tough=True,unpreventable=True),effect)),
        AbilityFactory.AfterUnitUseBasicPower(AbilityType.AlterEgoResponse,"You",RemoveThisFromGame,powers=["REC"]),
    ]
