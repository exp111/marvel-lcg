from . import *

# Lay Low
def GetAbilities():
    def lay_low(effect,message):
        Players.ForEachPlayer(effect,lambda player: YouMayFlipToYourAlterEgoForm(player,effect))
        for identity in Worlds.GetOnFieldAlterEgos(effect):
            effect.this.HealthUnits([identity],identity.CastTo(AlterEgo).recover,effect)
    return [AbilityFactory.WhenSchemeBeDefeated(AbilityType.WhenDefeated,"This",lay_low)]
