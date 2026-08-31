from . import *

# Inspiring Pottery


def GetAbilities() -> Sequence['Ability']:
    return ArtAttachmentAbilities(stalwart=True, resource="G")
