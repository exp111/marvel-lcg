from . import *

# Adamantium-Laced Spine


def GetAbilities() -> Sequence['Ability']:
    def adamantium_laced_spine(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldTakeDamage',
    ) -> None:
        this = effect.this.CastTo(Attachment)
        prevented_damage = max(0, message.will_take_damage - 3)
        if prevented_damage == 0:
            return

        message.PreventDamage(prevented_damage, effect)
        Faces.PlaceCountersOn([this], prevented_damage, 'damage', effect)
        if this.GetCounters('damage') >= 6:
            this.card.Flip(effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(BULLSEYE),
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            BULLSEYE,
            adamantium_laced_spine,
        ),
    ]
