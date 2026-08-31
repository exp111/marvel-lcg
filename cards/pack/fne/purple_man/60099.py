from . import *


def GetAbilities() -> Sequence['Ability']:
    return PurpleManVillainAbilities(villainous=True, patrol=True)
