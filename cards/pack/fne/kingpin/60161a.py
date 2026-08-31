from . import *
from cards.pack.fne.campaign import CampaignSetup


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        Unused(message)
        for player in Worlds.GetPlayers(effect):
            RevealSetupNemesis(player, effect)

    return [
        AbilityFactory.WhenCardSetup("This", setup),
        *CampaignSetup("Kingpin"),
    ]
