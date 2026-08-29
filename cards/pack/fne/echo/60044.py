from . import *


def GetAbilities() -> Sequence['Ability']:
    def choreography(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        player = effect.GetInitiator()
        Faces.ShuffleAllTo(effect.targets, player.player_deck, effect)
        if player.IsAlterEgo():
            player.DrawUp(1, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            choreography,
        ).SetCostFunc(CostFunc.Exhaust("This")).SetTarget(
            ASPECT_OR_BASIC_EVENT,
            from_where=["YourDiscardPile"],
        ),
    ]
