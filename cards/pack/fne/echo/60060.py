from . import *


def GetAbilities() -> Sequence['Ability']:
    def raised_by_the_kingpin_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        Find.FindAndPutIntoPlay(
            effect,
            message.GetToPlayer(),
            name="Kingpin",
            card_type=Minion,
        )

    def record_thwart(
        effect: 'Effect',
        message: 'Message.AfterUnitThwartEnd',
    ) -> None:
        this = effect.this.CastTo(Obligation)
        Faces.PlaceTokensOn(
            [this],
            message.total_remove_threat,
            "threat",
            effect,
        )
        if this.GetTokens("threat") >= 4:
            Faces.RemoveAllFromGame([this], effect)

    return [
        AbilityFactory.PlayersCannotDamageUnit(
            "You",
            CardFinder(name="Kingpin", card_type=Minion),
        ),
        AbilityFactory.WhenThisRevealed(
            None,
            raised_by_the_kingpin_revealed,
        ),
        AbilityFactory.AfterUnitThwartEnd(
            AbilityType.Response,
            "You",
            record_thwart,
        ),
    ]
