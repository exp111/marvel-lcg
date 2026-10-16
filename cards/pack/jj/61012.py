from . import *

# "Now I'm Ticked Off!"
from .helpers import PlaceEvidence

def GetAbilities():
    def ticked_off(effect,message):
        player=message.GetToPlayer()
        effect.GetInitiator().GetIdentity().ChangeToForm(Hero,effect)
        enemies=[message.trigger,*player.GetEngagedMinions()]
        effect.this.DealDamage(enemies,5,effect)
        Faces.DiscardAll([effect.this],effect)
    return [AbilityFactory.AfterEnemyActivationEnd(AbilityType.ForcedResponse,Villain,ticked_off,
        conditions=[lambda effect,message: AlterEgo.IsType(effect.GetInitiator().GetIdentity())])
        .SetLabel("attack")]
