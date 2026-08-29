from . import *


def GetAbilities() -> Sequence['Ability']:
    def serve(effect: 'Effect', player: 'Player') -> None:
        effect.this.PlaceThreatOnSchemes("MainScheme", 2, effect)

    return PurpleCommandAbility("Exhaust this card and remove 1 command counter → place 2 threat on the main scheme", serve)
