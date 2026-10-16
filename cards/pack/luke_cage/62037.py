from . import *

# Black Belt
def GetAbilities():
    return [*AbilityFactory.GiveKeywordToAttached(Friend,health=1,trait="MARTIAL ARTIST"),
        AbilityFactory.CanPlayThisUpgradeCard(Friend,conditions=[lambda effect,message:
            any(face.HasTrait("MARTIAL ARTIST") and Player.IsType(face.GetControlBy())
                for face in effect.world.FindCardsOnField())])]
