from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        leader = Worlds.GetEnemyLeader(effect)
        if leader:
            leader.DoActivate(player, effect)
            Faces.GiveStatus([leader], "Tough", effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
