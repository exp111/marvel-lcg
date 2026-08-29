from . import *


def GetAbilities() -> Sequence['Ability']:
    def master_manipulator_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        Find.FindAndPutIntoPlay(
            effect,
            message.GetToPlayer(),
            name="Kingpin",
            card_type=Minion,
        )

    return [
        AbilityFactory.UnitCannotTakeDamageWhile(
            AbilityType.NonKeyword,
            CardFinder(name="Kingpin", card_type=Minion),
        ),
        AbilityFactory.WhenThisRevealed(
            None,
            master_manipulator_revealed,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            RevealThisCard,
            conditions=[
                lambda effect, message:
                    Worlds.FindCardOnField(
                        effect,
                        name="Kingpin",
                        card_type=Minion,
                    ) is not None,
            ],
        ),
    ]
