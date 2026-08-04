from . import *

# Pacifism

def GetAbilities() -> Sequence['Ability']:

    def discard_by_tucked_cards(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        this = effect.this.CastTo(Obligation)
        ionic = FindIonicPhysiology(effect)
        if not ionic:
            return
        chosen = effect.GetInitiator().AskDiscardFaces(
            ionic.GetPlacedCardArea().GetAll(),
            (3, 3),
            effect,
        )
        if len(chosen) == 3:
            Faces.DiscardAll([this], effect)

    return [
        *AbilityFactory.UnitCannotAttackTarget(
            "AttachedIdentity",
            cannot_attack=True,
            cannot_trigger_attack_ability=True,
        ),
        AbilityFactory.PlayerActionToDiscardThis(
            AbilityType.AlterEgoAction,
        ).SetCostFunc(CostFunc.Exhaust("YourIdentity")),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.AlterEgoAction,
            discard_by_tucked_cards,
            conditions=[
                lambda effect, message:
                    FindIonicPhysiology(effect) is not None and
                    FindIonicPhysiology(effect).GetPlacedCardArea().GetSize() >= 3,
            ],
        ),
    ]
