from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        Unused(message)
        for player in Worlds.GetPlayers(effect):
            if not FindAndRevealNemesisForEndgame(player, effect):
                RevealUnderlingNotInPlay(player, effect)
        if Worlds.IsExpert(effect):
            Find.FindAndReveal(
                effect,
                Worlds.GetFirstPlayer(effect),
                who_perform=Worlds.GetFirstPlayer(effect),
                name="Organized Crime",
                card_type=SideScheme,
            )

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
