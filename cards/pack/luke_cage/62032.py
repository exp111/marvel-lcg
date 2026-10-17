from . import *

# Asp
def GetAbilities():
    return [
        AbilityFactory.AfterUnitSchemeEnd(AbilityType.ForcedResponse,"This",
            lambda effect,message: Faces.GiveStatus([message.against_player.GetIdentity()],"Stunned",effect)),
        AbilityFactory.WhenCardBecomeBoost("This",
            lambda effect,message: Faces.GiveStatus([message.GetToPlayer().GetIdentity()],"Stunned",effect)),
    ]
