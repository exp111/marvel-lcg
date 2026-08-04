from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        effect.this.CastTo(Minion).DoActivate(message.GetToPlayer(), effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
