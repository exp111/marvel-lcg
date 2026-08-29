from . import *


def GetAbilities() -> Sequence['Ability']:
    return DisasterEnvironmentAbilities(
        "R",
        lambda character: Unit2.IsType(character) and character.IsTough(),
    )
