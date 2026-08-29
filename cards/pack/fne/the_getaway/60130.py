from . import *


def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.ThisGainKeyword(
            SpeedThreshold(3),
            toughness=1,
            change_on_event=SPEED_EVENT,
        ),
        AbilityFactory.ThisGainKeyword(
            SpeedThreshold(6),
            quickstrike=1,
            change_on_event=SPEED_EVENT,
        ),
        AbilityFactory.ThisGainKeyword(
            SpeedThreshold(9),
            surge=1,
            change_on_event=SPEED_EVENT,
        ),
    ]
