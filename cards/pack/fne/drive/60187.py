from . import *


def GetAbilities() -> Sequence['Ability']:
    return VehicleAttachmentAbilities(3, highest_sch=True)
