from . import *


def GetAbilities() -> Sequence['Ability']:
    def lose_stilt_instead(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldTakeDamage',
    ) -> None:
        message.SetBeInstead(effect)
        Faces.RemoveCountersOn([effect.this], 1, "stilt", effect)

    return [
        AbilityFactory.ThisEnterPlayWithCounters(2, "stilt"),
        AbilityFactory.ThisGainKeyword(
            lambda effect, ui: effect.this.GetCounters("stilt"),
            attack=1,
            scheme=1,
            change_on_event=OnEvent.Counter("This", "stilt"),
        ),
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            "This",
            lose_stilt_instead,
            conditions=[
                lambda effect, message:
                    effect.this.GetCounters("stilt") > 0,
            ],
        ),
    ]
