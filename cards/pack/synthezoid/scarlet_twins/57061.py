from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        identity = message.GetToPlayer().GetIdentity()
        if not Faces.GiveStatus([identity], "Confused", effect):
            effect.this.PlaceThreatOnSchemes("MainScheme", 2, effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
