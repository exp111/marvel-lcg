from . import *

# "Now I'm Ticked Off!"
from .helpers import PlaceEvidence

def GetAbilities():
    def ticked_off(effect,message):
        player=message.GetToPlayer()
        effect.GetInitiator().GetIdentity().ChangeToForm(Hero,effect)
        enemies=[face for face in [message.trigger,*player.GetEngagedMinions()]
            if face.CanBeAttackBy(effect)]
        effect.this.DealDamage(enemies,5,effect)
        Faces.DiscardAll([effect.this],effect)
    return [AbilityFactory.AfterEnemyActivationEnd(AbilityType.ForcedResponse,Villain,ticked_off,
        conditions=[lambda effect,message: AlterEgo.IsType(effect.GetInitiator().GetIdentity())])
        .SetLabel("attack")]
