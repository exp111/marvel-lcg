from . import *

# Cop


def GetAbilities() -> Sequence['Ability']:
    def cop_would_scheme(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldScheme',
    ) -> None:
        this = effect.this.CastTo(Minion)
        villain = Worlds.FindVillain(effect)
        message.SetBeInstead(effect)
        if villain:
            this.BasicAttack([villain], effect)

    def cop_defeated(
        effect: 'Effect',
        message: 'Message.WhenUnitBeDefeated',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(Minion)
        this.PlaceThreatOnSchemes("MainScheme", 2, effect)

    return [
        AbilityFactory.WhenUnitWouldScheme(
            AbilityType.ForcedInterrupt,
            "This",
            cop_would_scheme,
        ),
        AbilityFactory.WhenUnitBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            cop_defeated,
        ),
    ]
