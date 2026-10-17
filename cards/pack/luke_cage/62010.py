from . import *

# Metal Bracer
def GetAbilities():
    return [
        *AbilityFactory.GiveKeywordToAttached(CardFinder(name="Luke Cage"),retaliate=1),
        AbilityFactory.WhenFaceWouldDealDamage(AbilityType.HeroInterrupt,None,
            lambda effect,message: message.IncreaseDamage(-1,effect),
            who_take_damage=CardFinder(name="Luke Cage"),include_overkill=True,
            conditions=[lambda effect,message: not message.property.unpreventable])
        .SetCostFunc(CostFunc.Exhaust("This")),
    ]
