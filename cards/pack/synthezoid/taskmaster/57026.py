from . import *

def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        leader = Worlds.GetEnemyLeader(effect)
        if leader:
            Faces.GiveStatus([leader], "Tough", effect)
            Faces.GiveFacedownBoostCards([leader], 1, effect)
    return [AbilityFactory.WhenSchemeBeDefeated(AbilityType.WhenDefeated, "This", defeated)]
