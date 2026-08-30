from . import *


def GetAbilities() -> Sequence['Ability']:
    return [SearchRewardAfterMulligans(Support, "support")]
