from . import *

# "Stand with Me!"
def GetAbilities():
    def stand(effect,message):
        identity=effect.GetInitiator().GetIdentity()
        Faces.GiveStatus([identity],"Tough",effect)
        effect.this.RemoveThreatFromSchemes(effect.targets,min(5,identity.tough),effect)
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,stand)
        .SetPlay().SetLabel("thwart").SetTarget(Scheme2)]
