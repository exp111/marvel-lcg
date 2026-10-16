from . import *

# Luke Cage
from .helpers import UnbreakableSkin

def GetAbilities():
    def burstein(effect,message):
        player=effect.GetInitiator()
        face=Search.PlayerCard(effect,player,include_player_deck=True,include_discard_pile=True,
            card_type=Upgrade,name="Burstein Process")
        if face: player.GainCard(face,effect)
    return [*UnbreakableSkin(),AbilityFactory.WhenInYourPlayTurn(AbilityType.Action,burstein).LimitOncePerPhase()]
