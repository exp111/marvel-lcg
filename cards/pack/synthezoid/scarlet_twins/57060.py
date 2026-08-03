from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        identity = message.GetToPlayer().GetIdentity()
        if not Faces.GiveStatus([identity], "Stunned", effect):
            effect.this.DealDamage([identity], 2, effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
