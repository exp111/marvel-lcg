from . import *

# Cruisin' for a Bruisin'
def GetAbilities():
    def engage(effect,message):
        effect.this.CastTo(Upgrade).GetBindFace().CastTo(Minion).EngagePlayer(effect.GetInitiator(),effect)
    return [
        AbilityFactory.CanPlayThisUpgradeCard(Minion),
        AbilityFactory.WhenUnitWouldAttackUnit(AbilityType.NonKeyword,None,"AttachedEnemy",
            lambda effect,message: message.IncreaseDamage(2,effect)),
        AbilityFactory.UnitAttackGainKeyword(None,"AttachedEnemy",overkill=True),
        AbilityFactory.AfterYouPlayThisFromHand(AbilityType.Response,engage),
    ]
