from . import *

# Art Museum Heist 1A


def GetAbilities() -> Sequence['Ability']:
    def art_museum_heist_setup(
        effect: 'Effect',
        message: 'Message.WhenCardSetup',
    ) -> None:
        Unused(message)
        villain = Worlds.FindVillain(effect)
        if villain:
            SetupCards.AttachTo(
                effect,
                villain,
                trait="ART",
                card_type=Attachment,
                choose="Random",
                include_in_play=False,
                shuffle_others_into_encounter_deck=True,
            )

    return [
        AbilityFactory.WhenCardSetup(
            "This",
            art_museum_heist_setup,
        ),
    ]
