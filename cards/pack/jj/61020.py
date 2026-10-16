from . import *

# Run Them to Ground


def GetAbilities():
    def run_them_to_ground(effect, message):
        effect.world.phase.SkipNextVillainPhase()
        Players.ForEachPlayer(effect, lambda player: player.DealEncounterCards(1, effect))

        immunity = effect.this.effect.RegisterTemp(
            AbilityFactory.WhenUnitWouldTakeDamage(
                AbilityType.Temp0, Villain,
                lambda effect, message: message.SetBeInstead(effect),
            ),
            unregister_after_exec=False,
        )

        def end_immunity(effect, message):
            for protection in immunity:
                protection.UnRegisterSelf()

        effect.this.effect.RegisterTemp(
            AbilityFactory.WhenVillainPhaseBegin(AbilityType.Temp0, end_immunity),
            unregister_after_exec=True,
        )

    return [AbilityFactory.WhenSchemeBeDefeated(
        AbilityType.WhenDefeated, "This", run_them_to_ground,
    )]
