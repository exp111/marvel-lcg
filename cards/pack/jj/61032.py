from . import *

# Indomitable Will
def GetAbilities():
    suggestion=CardFinder(card_type=Obligation,check_face_fn=lambda face: face.paper.card_id in ("61033a","61033b","61033c"))
    return [
        AbilityFactory.WhenThisRevealed(None,lambda effect,message:
            Faces.PlaceCountersOn(effect.world.FindCardsOnField(finder=suggestion),2,"pheromone",effect)),
        AbilityFactory.AfterCardEnterPlay(AbilityType.ForcedResponse,suggestion,
            lambda effect,message: Faces.PlaceCountersOn([message.trigger],2,"pheromone",effect)),
    ]
