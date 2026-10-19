from . import *

# Guerilla Warfare
def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.AfterStatusCardPlaceOn(
            AbilityType.ForcedResponse,
            "EnemyLeader",
            None,
            lambda effect, message: effect.this.PlaceThreatOnSchemes([effect.this], 1, effect),
        ),
    ]
