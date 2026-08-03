from . import *

# * Mr. Hollywood

def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.CanGenerateResources(
            AbilityType.Resource,
            Resources("Y"),
            is_play_card=True,
        ).LimitOncePerEvent(),
    ]
