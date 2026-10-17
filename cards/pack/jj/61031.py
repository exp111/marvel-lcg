from . import *

# Purple Man
def GetAbilities():
    others=CardFinder(card_type=Unit2,check_face_fn=lambda face: face.paper.card_id != "61031")
    def highest(effect,fields):
        faces=effect.world.FindCardsOnField(finder=others)
        return max((getattr(face,field,0) for face in faces for field in fields),default=0),False
    return [
        AbilityFactory.ThisSetKeyword(lambda effect,ui: highest(effect,["attack"]),attack=1,
            change_on_event=OnEvent.CardKeyword(others)),
        AbilityFactory.ThisSetKeyword(lambda effect,ui: highest(effect,["scheme","thwart"]),scheme=1,
            change_on_event=OnEvent.CardKeyword(others)),
    ]
