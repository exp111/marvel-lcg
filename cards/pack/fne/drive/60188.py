from . import *


def GetAbilities() -> Sequence['Ability']:
    return VehicleAttachmentAbilities(6, fewest_remaining_hp=True)
