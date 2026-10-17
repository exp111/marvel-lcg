from . import *

# Snooping Around
from .helpers import PlaceEvidence

def GetAbilities():
    def snoop(effect, message):
        effect.this.RemoveThreatFromSchemes(effect.targets, 4, effect)
        PlaceEvidence(effect, 2)
        face=Worlds.DiscardEncounterTopCard(effect)
        if face:
            if Minion.IsType(face) or EncounterSideScheme.IsType(face):
                face.Reveal(effect.GetInitiator(), effect)
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.AlterEgoAction, snoop)
            .SetPlay().SetLabel("thwart").SetTarget(Scheme2)
            .SetHasNoTargetEffect()]
