from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        leader = Worlds.GetEnemyLeader(effect)
        if leader:
            leader.DoActivate(message.GetToPlayer(), effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
