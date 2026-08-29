from . import *


def GetAbilities() -> Sequence['Ability']:
    return VehicleAttachmentAbilities(4, highest_atk=True)
