from . import *


def GetAbilities() -> Sequence['Ability']:
    return KingpinStageTwoAbilities(expert=True)
