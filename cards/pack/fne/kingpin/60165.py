from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        Unused(message)
        kingpin = GetKingpin(effect)
        if kingpin:
            kingpin.GiveFacedownBoostCardsInternal(1, effect, None)

    def discard_and_scheme(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        Unused(message)
        player = effect.GetInitiator()
        Faces.DiscardAll([effect.this], effect)
        kingpin = GetKingpin(effect)
        if kingpin:
            kingpin.DoSchemes(player, effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        Unused(message)
        kingpin = GetKingpin(effect)
        if kingpin:
            effect.this.CastTo(Attachment).AttachTo2(kingpin, effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(KINGPIN),
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            discard_and_scheme,
        ).SetCostFunc(CostFunc.Discard(
            "YourHandCards",
            card_type=Event,
            trait="THWART",
        )).SetName(
            "Discard a THWART event → discard James Wesley and Kingpin schemes"
        ).AnyPlayerCanDoThis(),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
