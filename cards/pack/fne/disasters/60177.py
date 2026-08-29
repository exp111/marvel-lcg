from . import *


def GetAbilities() -> Sequence['Ability']:
    return DisasterEnvironmentAbilities(
        "G",
        lambda character: character.HasTrait("MYSTIC"),
    )
