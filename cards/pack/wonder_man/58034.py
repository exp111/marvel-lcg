from . import *

# Avengers Compound

def GetAbilities() -> Sequence['Ability']:

    def can_use_avengers_compound(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> bool:
        this = effect.this.CastTo(Support)
        if this.GetPlacedCardArea().GetSize() > 0:
            return True
        return any(Ally.IsType(face) for face in effect.GetInitiator().hand_cards.Get(True))

    def avengers_compound(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        this = effect.this.CastTo(Support)
        initiator = effect.GetInitiator()
        tucked = this.GetPlacedCardArea().GetAll()

        if tucked:
            initiator.PlayCardsLikeInTurn(tucked, effect, forced=True)
            return

        initiator.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Tuck an ally from your hand under Avengers Compound",
                lambda targets: this.TuckCardUnderHere(targets, effect),
            ).SetTarget(Ally, from_where=["YourHandCards"]),
        )

    return [
        AbilityFactory.CanPlayThisSupportCard(
        ).SetPlay(only_if_your_identity_has_trait="AVENGER"),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.Action,
            avengers_compound,
            conditions=[can_use_avengers_compound],
        ).SetCostFunc(CostFunc.Exhaust("This")),
    ]
