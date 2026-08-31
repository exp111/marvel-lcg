from . import *


def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.UnitCannotTakeDamageWhile(
            AbilityType.NonKeyword,
            Villain,
        )
    ]
