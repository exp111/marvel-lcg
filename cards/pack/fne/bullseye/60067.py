from . import *

# * Bullseye (III)


def GetAbilities() -> Sequence['Ability']:
    def bullseye_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        Unused(message)
        SetupCards.Reveal(
            effect,
            name="Deranged Bloodlust",
            card_type=SchemeSide2,
            include_in_play=False,
        )

    return [
        AbilityFactory.WhenThisRevealed(
            None,
            bullseye_revealed,
        ),
        *BullseyeActivationAbilities(),
    ]
