from . import *


def GetAbilities() -> Sequence['Ability']:
    return [SearchRewardAfterMulligans(Ally, "ally")]
