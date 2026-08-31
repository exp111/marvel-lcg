from . import *


def GetAbilities() -> Sequence['Ability']:
    return TyphoidVillainAbilities(13, damage_each_identity=True)
