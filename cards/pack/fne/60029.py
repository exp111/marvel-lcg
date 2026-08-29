from . import *

# * Stick


def GetAbilities() -> Sequence['Ability']:

    def stick(effect: 'Effect', message: 'Message.WhenUnitUseBasicPower') -> None:
        this = effect.this.CastTo(Support)
        player = effect.GetInitiator()

        def reduce_and_ready(targets: Sequence['CardFace']) -> None:
            message.GainValue(-1, effect)
            Faces.ReadyAll([this], effect)

        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Exhaust Stick to give the character +1 to this basic power",
                lambda targets: message.GainValue(+1, effect),
            ).SetCostFunc(CostFunc.Exhaust("This")),
            AbilityFactory.ForChoiceAbility(
                "Give the character -1 to this basic power and ready Stick",
                reduce_and_ready,
            ),
        )

    return [
        AbilityFactory.WhenUnitUseBasicPower(
            AbilityType.Interrupt,
            CardFinder2("MARTIAL ARTIST", Friend),
            stick,
        ),
    ]
