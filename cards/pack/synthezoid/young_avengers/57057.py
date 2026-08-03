from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        message.GetToPlayer().DiscardControlCards(effect, support=True)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
