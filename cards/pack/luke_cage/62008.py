from . import *

# Burstein Process
def GetAbilities():
    def process(effect,message):
        identity=effect.GetInitiator().GetIdentity()
        count=2 if identity.tough==0 else 1
        for _ in range(count): Faces.GiveStatus([identity],"Tough",effect)
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.AlterEgoAction,process)
        .SetCostFunc(CostFunc.Exhaust("This")).SetTarget("YourIdentity",canbe_tough=True)]
