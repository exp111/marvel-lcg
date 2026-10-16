from . import *

# Hellcat
def GetAbilities():
    def hellcat(effect,message):
        this=effect.this
        if this.PutIntoPlay(effect.GetInitiator(),effect,under_control=True):
            RunAt.TheEndOfThePhase(effect,lambda: Faces.DiscardAll([this],effect) if this.IsInPlay() else None)
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.Action,hellcat,
        conditions=[lambda effect,message: effect.GetInitiator().GetIdentity().HasTrait("DEFENDER")])
        .CanWorkOnlyInHand()]
