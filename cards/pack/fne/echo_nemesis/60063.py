from . import *


def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.UnitCannotTakeDamageWhile(
            AbilityType.NonKeyword,
            CardFinder(name="Kingpin", card_type=Minion),
        ),
    ]
