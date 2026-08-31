from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        minion = Filter.One(Worlds.GetOnFieldMinions(effect), effect, fewest_remaining_hp=True)
        if minion:
            Faces.DefeatUnits([minion], this, effect)
        discarded = Worlds.DiscardEncounterCardsUntil(effect, card_type=Minion)
        if discarded:
            discarded.Reveal(message.GetToPlayer(), effect)

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
