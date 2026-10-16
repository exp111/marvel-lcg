from . import *

# Hellcat
def GetAbilities():
    def hellcat(effect,message):
        this=effect.this
        if this.PutIntoPlay(effect.GetInitiator(),effect,under_control=True):
            # Leaving play ends this instance's delayed discard, even if the
            # same physical card is played normally again before phase end.
            this.effect.RegisterTemp(
                AbilityFactory.WhenPhaseEnd(AbilityType.Temp2, None,
                    lambda followup, ended: Faces.DiscardAll([this], followup)),
                unregister_after_exec=True, until_this_leave_play=True,
            )
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.Action,hellcat,
        conditions=[lambda effect,message: effect.GetInitiator().GetIdentity().HasTrait("DEFENDER")])
        .CanWorkOnlyInHand()]
