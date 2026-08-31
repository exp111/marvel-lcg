from . import *


def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenUnitBeDefeated') -> None:
        effect.this.PlaceThreatOnSchemes("MainScheme", 3, effect)

    return [InfluencedMinionDefeated(defeated)]
