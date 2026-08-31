from . import *
from cards.pack.fne.campaign import CampaignSetup


def GetAbilities() -> Sequence['Ability']:
    return [
        *GetSetupAbilities(),
        *CampaignSetup("Protection Racket"),
    ]
