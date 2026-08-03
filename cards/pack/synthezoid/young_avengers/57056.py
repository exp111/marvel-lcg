from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        message.GetToPlayer().DiscardControlCards(effect, upgrade=True)
    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.UnitAttackGainKeyword("This", piercing=True, ranged=True),
    ]
