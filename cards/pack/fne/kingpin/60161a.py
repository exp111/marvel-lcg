from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        Unused(message)
        for player in Worlds.GetPlayers(effect):
            RevealSetupNemesis(player, effect)

    return [AbilityFactory.WhenCardSetup("This", setup)]
