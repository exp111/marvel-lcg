from . import *


def GetAbilities() -> Sequence['Ability']:

    def daredevils_billy_club(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        player = effect.GetInitiator()
        this = effect.this.CastTo(Upgrade)
        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Deal 1 damage to an enemy",
                lambda targets: this.DealDamage(targets, 1, effect),
            ).SetTarget(Enemy),
            AbilityFactory.ForChoiceAbility(
                "Daredevil gains the Aerial trait until the end of the round",
                lambda targets: targets[0].GainUntilRoundEnd(effect, trait="AERIAL"),
            ).SetTarget(CardFinder(name="Daredevil", card_type=Hero)),
        )

    return [
        AbilityFactory.CanPlayThisUpgradeCard(),
        *AbilityFactory.GiveKeywordToInPlayWhenApplyThis(
            CardFinder(name="Daredevil", card_type=Hero),
            attack=1,
        ),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            daredevils_billy_club,
        ).SetCostFunc(CostFunc.ReturnToHand("This", to_who="Initiator")),
    ]
