from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        Unused(message)
        SetupCards.PutIntoPlay(
            effect,
            name="Daily Bugle",
            card_type=Environment,
        )

        available = list(Worlds.GetSetAsideAreaCards(effect, DAILY_BUGLE_SUPPORT))
        for player in Worlds.GetPlayers(effect):
            if not available:
                break
            support = Rand.RandomChoice(available, effect)
            available.remove(support)
            support.PutIntoPlay(player, effect, under_control=True)

        Faces.RemoveAllFromGame(available, effect)

    return [AbilityFactory.WhenCardSetup("This", setup)]
