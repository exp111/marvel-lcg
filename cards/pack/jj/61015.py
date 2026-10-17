from . import *

# Captain Marvel
def GetAbilities():
    def captain_marvel(effect,message):
        player=effect.GetInitiator()
        discarded=player.DiscardDeckTopCards(4,effect)
        energy=FacesCounter.GetPrintedResourcesCount(discarded,"Y")
        if energy:
            player.ChooseAbilities(effect,AbilityFactory.ForChoiceAbility("Remove 2 threat",
                lambda targets: effect.this.RemoveThreatFromSchemes(targets,2,effect)).SetTarget(Scheme2))
        if energy>1:
            player.ChooseAbilities(effect,AbilityFactory.ForChoiceAbility("Confuse an enemy",
                lambda targets: Faces.GiveStatus(targets,"Confused",effect)).SetTarget(Enemy,canbe_confused=True))
    return [AbilityFactory.AfterCardEnterPlay(AbilityType.Response,"This",captain_marvel)]
