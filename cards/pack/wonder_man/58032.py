from . import *

# Coordinated Effort

def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.CanPlayThisUpgradeCard(
            CardFinder(card_type=EncounterNonVillainCard),
        ),
    ]

