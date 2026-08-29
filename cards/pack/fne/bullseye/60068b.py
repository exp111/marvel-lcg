from . import *

# Damaged Spine


def GetAbilities() -> Sequence['Ability']:
    def damaged_spine(
        effect: 'Effect',
        message: 'Message.AfterUnitSchemeEnd',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(Attachment)
        Faces.RemoveCountersOn([this], 3, 'damage', effect)
        if this.GetCounters('damage') == 0:
            this.card.Flip(effect)

    return [
        AbilityFactory.AfterUnitSchemeEnd(
            AbilityType.ForcedResponse,
            BULLSEYE,
            damaged_spine,
        ),
    ]
