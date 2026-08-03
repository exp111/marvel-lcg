from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        effect.this.PlaceThreatOnSchemes("MainScheme", 2, effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed)]
