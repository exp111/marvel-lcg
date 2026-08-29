from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        Unused(message)
        villain = Worlds.FindVillain(effect)
        if villain:
            SetupCards.AttachTo(
                effect,
                villain,
                name="Master Key",
                card_type=Attachment,
                include_in_play=False,
            )
        for player in Worlds.GetPlayers(effect):
            prisoner = Worlds.DiscardEncounterCardsUntil(
                effect,
                trait="PRISONER",
                card_type=Minion,
            )
            if prisoner:
                prisoner.Reveal(player, effect)

    return [AbilityFactory.WhenCardSetup("This", setup)]
