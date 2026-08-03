from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        Faces.GiveStatus([message.GetToPlayer().GetIdentity()], "Stunned", effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
