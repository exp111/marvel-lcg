from . import *


def GetAbilities() -> Sequence['Ability']:

    def the_man_without_fear(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        player = effect.GetInitiator()
        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Choose any Sense upgrade and play it, ignoring its resource cost",
                lambda targets: ChooseAndPlaySenseUpgrade(
                    player,
                    effect,
                    ignore_resources_cost=True,
                    force_choice=True,
                ),
                condition=bool(GetPlayableSenseCards(player, effect)),
            ).SetHasNoTargetEffect(),
            AbilityFactory.ForChoiceAbility(
                "Ready Daredevil",
                lambda targets: Faces.ReadyAll(targets, effect),
            ).SetTarget(
                CardFinder(name="Daredevil", card_type=Hero, canbe_ready=True),
            ),
        )

    return [
        AbilityFactory.CanPlayThisUpgradeCard(),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            the_man_without_fear,
        ).SetCostFunc(CostFunc.Exhaust("This"))
        .SetCostFunc(CostFunc.TakeDamage(1, "YourIdentity")),
    ]
