from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        face = Worlds.GetEncounterDiscardPile(effect).FindTopmost(CardFinder(card_type=Treachery))
        if face:
            face.ResolveAbility(message.GetToPlayer(), AbilityType.WhenRevealed, effect)
    return [AbilityFactory.WhenThisRevealed(None, revealed).LimitOncePerRound()]
