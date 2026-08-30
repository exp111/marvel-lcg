from . import *


def GetAbilities() -> Sequence['Ability']:
    return [SearchRewardAfterMulligans(Upgrade, "upgrade")]
