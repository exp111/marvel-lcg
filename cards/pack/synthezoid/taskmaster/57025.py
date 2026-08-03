from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        leader = Worlds.GetEnemyLeader(effect)
        if leader:
            Faces.GiveStatus([leader], "Tough", effect)
            Faces.GiveFacedownBoostCards([leader], 1, effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
