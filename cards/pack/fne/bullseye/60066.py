from . import *

# * Bullseye (II)


def GetAbilities() -> Sequence['Ability']:
    def bullseye_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(EncounterVillain)
        SetupCards.AttachTo(
            effect,
            this,
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
