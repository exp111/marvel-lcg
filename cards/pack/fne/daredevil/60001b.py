from . import *


def GetAbilities() -> Sequence['Ability']:
    return [
        AbilityFactory.BeginGameWithSetAside(
            SENSE_CARD_IDS,
            SetupSenseDeck,
        ),
        *SenseDeckRuleAbilities(),
    ]
