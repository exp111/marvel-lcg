from . import *


def GetAbilities() -> Sequence['Ability']:
    def round_end(effect: 'Effect', message: 'Message.WhenRoundEnd') -> None:
        Unused(message)
        this = effect.this.CastTo(MainScheme)
        if this.threat <= 0:
            return
        Faces.PlaceCountersOn([this], 1, "speed", effect)
        alongside = Worlds.FindCardOnField(
            effect,
            CardFinder(name="Alongside", card_type=Attachment),
        )
        if alongside:
            alongside.card.Flip(effect)
        else:
            Faces.PlaceCountersOn([this], 1, "speed", effect)

    return [
        AbilityFactory.WhenRoundEnd(
            AbilityType.ForcedInterrupt,
            None,
            round_end,
        ),
    ]
