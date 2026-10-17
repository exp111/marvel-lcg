from . import *

# Breakthrough
from .helpers import Alias

def GetAbilities():
    def breakthrough(effect, message):
        player=effect.GetInitiator()
        Faces.ReadyAll([player.GetIdentity()], effect)
        Faces.ShuffleAllTo([effect.this], player.player_deck, effect)
    return [AbilityFactory.AfterCounterPlacedOn(AbilityType.Response,
        CardFinder(name="Alias Investigations"), "evidence", breakthrough,
        conditions=[lambda effect, message: message.trigger == Alias(effect) and message.counters > 0]
    ).SetPlay()]
