from . import *


def GetAbilities() -> Sequence['Ability']:
    def flip_if_threshold(effect: 'Effect', message: 'Message.AfterUnitTookDamage') -> None:
        Unused(message)
        loki = effect.this.CastTo(Villain)
        threshold = Worlds.ConvertPerPlayerIconToInt("10*", effect)
        if loki.health <= threshold and loki.card.face == loki:
            loki.card.Flip(
                GameRule(loki, initiator=effect.world.GetFirstPlayer()),
            )

    def flip_instead_of_defeat(effect: 'Effect', message: 'Message.WhenUnitWouldBeDefeated') -> None:
        loki = effect.this.CastTo(Villain)
        message.SetBeInstead(effect)
        loki.SetHealth(1, effect)
        loki.card.Flip(
            GameRule(loki, initiator=effect.world.GetFirstPlayer()),
        )

    return [
        AbilityFactory.AfterUnitTookDamage(
            AbilityType.ForcedResponse,
            "This",
            flip_if_threshold,
        ),
        AbilityFactory.WhenUnitWouldBeDefeated(
            AbilityType.ForcedInterrupt,
            "This",
            flip_instead_of_defeat,
        ),
    ]
