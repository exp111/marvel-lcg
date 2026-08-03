from . import *

# Energy Siphon

def GetAbilities() -> Sequence['Ability']:

    def available_resources(effect: 'Effect', message: 'Message.CheckPlayerCanPayCost') -> 'Resources':
        health = effect.GetInitiator().GetIdentity().health
        return Resources("Y") + (Resources("Y") * min(3, health))

    def generated_resources(effect: 'Effect', message: 'Message.WhenPlayerPayingResources') -> 'Resources':
        damage = effect.cost_func.Get(CostFunc.TakeDamageUpToHealth).return_damage
        return Resources("Y") + (Resources("Y") * damage)

    return [
        AbilityFactory.DoDiscardThisToGenerateResources(
            AbilityType.HeroInterrupt,
            res_fn=generated_resources,
        ).SetCostFunc(CostFunc.TakeDamageUpToHealth("YourIdentity", min_damage=0, max_damage=3)),
        AbilityFactory.CheckThisCanDropPay(
            available_resources,
            spend_this_only_in_hero_form=True,
        ),
    ]
