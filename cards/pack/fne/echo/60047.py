from . import *


def GetAbilities() -> Sequence['Ability']:
    def muscle_memory(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        Faces.AddToHand(effect.targets, effect.GetInitiator(), effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            muscle_memory,
            conditions=[
                lambda effect, message:
                    effect.GetInitiator().GetIdentity()
                    .GetPlacedCardArea().GetSize() > 0,
            ],
        ).SetCostFunc(CostFunc.Exhaust("This")).SetTarget(
            lambda effect:
                effect.GetInitiator().GetIdentity()
                .GetPlacedCardArea().GetAll(),
        ),
    ]
