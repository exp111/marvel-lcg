from . import *


def GetAbilities() -> Sequence['Ability']:
    return DisasterEnvironmentAbilities(
        "Y",
        lambda character: character.HasTrait("AERIAL"),
    )
