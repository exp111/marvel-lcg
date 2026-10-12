from core import *
from game.card.face import *
from game.ability import *
from game.message import *
from game.player import *
from cards.paper import Paper

@final
class EncounterSideScheme(SchemeSide2, CanCrisis, HasSetup, HasPermanent, EncounterNonVillainCard, FinalType):
    # Permanent schemes still resolve defeat abilities. DiscardInternal keeps
    # them in play unless their printed ability flips or moves them.
    @override
    def __init__(self, paper: 'Paper') -> None:
        super().__init__(paper)

