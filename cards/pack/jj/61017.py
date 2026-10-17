from . import *

# Squirrel Girl
def GetAbilities():
    def squirrels(effect,message):
        Faces.PlaceCountersOn([effect.this],min(4,len(effect.GetInitiator().hand_cards.Get())),"squirrel",effect)
    return [
        AbilityFactory.AfterPlayerPlayedCard(AbilityType.Response,"You","This",squirrels,from_hand=True),
        AbilityFactory.WhenInYourPlayTurn(AbilityType.Action,
            lambda effect,message: effect.this.RemoveThreatFromSchemes(effect.targets,1,effect))
        .SetCostFunc(CostFunc.Counter("This",1,"squirrel")).SetTarget(Scheme2),
    ]
