from . import *

# Venomous Whispers
def GetAbilities():
    def whispers(effect,message):
        minion=Worlds.DiscardEncounterCardsUntil(effect,card_type=Minion,trait="SERPENT SOCIETY")
        if minion: minion.Reveal(message.defeating_player,effect)
    return [
        AbilityFactory.UnitCannotBeAttacked(CardFinder(card_type=Minion,trait="SERPENT SOCIETY")),
        AbilityFactory.WhenSchemeBeDefeated(AbilityType.WhenDefeated,"This",whispers,has_defeating_player=True),
        AbilityFactory.WhenCardBecomeBoost("This",lambda effect,message:
            Faces.GiveStatus([message.GetToPlayer().GetIdentity()],"Confused",effect)),
    ]
