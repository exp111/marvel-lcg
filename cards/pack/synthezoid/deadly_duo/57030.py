from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        face = Filter.One(player.GetControlCards(), effect, highest_cost=True)
        if face:
            Faces.DiscardAll([face], effect)
        else:
            ThisCardGainSurge(effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
