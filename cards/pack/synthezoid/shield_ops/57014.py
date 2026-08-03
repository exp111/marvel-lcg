from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        Faces.GiveStatus(Worlds.GetOnFieldEnemies(effect), "Tough", effect)
    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        enemy = message.activating_enemy
        if enemy:
            Faces.GiveStatus([enemy], "Tough", effect)
    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
