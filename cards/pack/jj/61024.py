from . import *

# Entrapment
def GetAbilities():
    def change_form_cost(targets, effect):
        player = effect.GetInitiator()
        player.GetIdentity().ChangeToForm(Hero, effect)
        return Hero.IsType(player.GetIdentity())

    def entrapment(effect,message):
        effect.this.DealDamage([message.trigger],message.placed_threat,effect)
    return [AbilityFactory.AfterUnitSchemeEnd(AbilityType.AlterEgoResponse,Villain,entrapment)
        .SetCostFunc(CostFunc.Custom(None, change_form_cost))
        .SetCostFunc(CostFunc.Discard("This")).SetLabel("attack")]
