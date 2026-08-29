from . import *


def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        Unused(message)
        this = effect.this.CastTo(MainScheme)
        Faces.PlaceCountersOn(
            [this],
            2 if Worlds.IsExpert(effect) else 1,
            "speed",
            effect,
        )
        villain = Worlds.FindVillain(effect)
        if villain:
            SetupCards.AttachTo(
                effect,
                villain,
                name="Out Front",
                card_type=Attachment,
                include_in_play=False,
            )

    return [AbilityFactory.WhenCardSetup("This", setup)]
