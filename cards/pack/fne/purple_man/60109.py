from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Treachery)
        faces = Worlds.GetEncounterDiscardPileCards(effect, INFLUENCED_MINION)
        if not faces:
            this.GainSurge(1, effect)
            return
        chosen = message.GetToPlayer().AskChooseFace(faces, effect, forced=True)
        if chosen:
            chosen.Reveal(message.GetToPlayer(), effect)

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
