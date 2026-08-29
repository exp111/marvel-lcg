from . import *


def GetAbilities() -> Sequence['Ability']:
    return ElectroVillainAbilities(3, 2, attach_charge=False)
