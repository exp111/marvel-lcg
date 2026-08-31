from . import *


def GetAbilities() -> Sequence['Ability']:
    def robbie(
        effect: 'Effect',
        message: 'Message.AfterPlayerDealEncounterCard',
    ) -> None:
        player = message.GetToPlayer()
        face = message.would_message.face
        Faces.LookAt([face], effect.GetInitiator(), effect)
        effect.GetInitiator().MayChooseOneAbility(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Discard that encounter card and deal that player another",
                lambda targets: (
                    Faces.DiscardAll(targets, effect),
                    player.DealEncounterCards(1, effect),
                ),
            ).SetTarget(
                [face],
                by_search=True,
                not_move=True,
                not_shuffle=True,
            ),
        )

    ability = AbilityFactory.AfterPlayerDealEncounterCard(
        AbilityType.Response,
        robbie,
    )
    for cost in StaminaCost():
        ability.SetCostFunc(cost)
    return [ability]
