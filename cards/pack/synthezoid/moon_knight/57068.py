from . import *

def GetAbilities() -> Sequence['Ability']:
    def defeated(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        face = Worlds.DiscardEncounterCardsUntil(effect, card_type=Treachery)
        if face:
            player = message.defeating_player or Worlds.GetFirstPlayer(effect)
            face.ResolveAbility(player, AbilityType.WhenRevealed, effect)
    return [AbilityFactory.WhenSchemeBeDefeated(AbilityType.WhenDefeated, "This", defeated)]
