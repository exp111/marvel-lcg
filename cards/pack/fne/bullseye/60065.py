from . import *

# * Bullseye (I)


def GetAbilities() -> Sequence['Ability']:
    def bullseye_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        Unused(message)
        SetupCards.SetAsideCards(
            effect,
            name="Adamantium-Laced Spine",
            card_type=Attachment,
        )

    return [
        AbilityFactory.WhenThisRevealed(
            None,
            bullseye_revealed,
        ),
        *BullseyeActivationAbilities(),
    ]
