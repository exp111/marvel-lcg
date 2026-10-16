from . import *

# Observe
def GetAbilities():
    def observe(effect,message):
        player=effect.GetInitiator()
        villain=Worlds.FindVillain(effect)
        if villain: villain.DoSchemes(player,effect)
        Faces.GiveStatus([player.GetIdentity()],"Tough",effect)
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,observe).SetPlay()]
