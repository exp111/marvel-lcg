from . import *

# Shakedown
def GetAbilities():
    def shakedown(effect,message):
        minion=message.who_took_damage.CastTo(Minion)
        amount=minion.base_scheme
        effect.GetInitiator().ChooseAbilities(effect,AbilityFactory.ForChoiceAbility("Remove threat equal to the minion's base SCH",
            lambda targets: effect.this.RemoveThreatFromSchemes(targets,amount,effect)).SetTarget(Scheme2))
    return [AbilityFactory.CanPlayThisUpgradeCard("Players"),
        AbilityFactory.AfterUnitDefeatedUnit(AbilityType.Response,"You",Minion,shakedown,
            is_from_attack=True,has_excess_damage=False)
        .SetCostFunc(CostFunc.Exhaust("This"))]
