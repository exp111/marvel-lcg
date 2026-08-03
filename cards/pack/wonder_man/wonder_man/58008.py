from . import *

# Jet Belt

def GetAbilities() -> Sequence['Ability']:

    def can_generate(effect: 'Effect', message: 'Message.CheckPlayerCanPayCost') -> 'Resources|None':
        ionic = FindIonicPhysiology(effect)
        if Event.IsType(message.paying_for_effect.this):
            return Resources("Y")
        if ionic and ionic.GetPlacedCardArea().GetSize() > 0:
            return Resources("Y")
        return None

    def spend_jet_belt(effect: 'Effect', message: 'Message.WhenPlayerPayingResources') -> None:
        if Event.IsType(message.for_effect.this):
            return
        ionic = FindIonicPhysiology(effect)
        if ionic:
            effect.GetInitiator().AskDiscardFaces(
                ionic.GetPlacedCardArea().GetAll(),
                (1, 1),
                effect,
            )

    return [
        AbilityFactory.CanGenerateResources(
            AbilityType.HeroResource,
            resources_fn=can_generate,
            ex_operation=spend_jet_belt,
        ).SetCostFunc(CostFunc.Exhaust("This")),
    ]

