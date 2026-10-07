from . import *

# Flight of the Valkyrior

def GetAbilities() -> Sequence['Ability']:

    def flight_of_the_valkyrior(effect: 'Effect', message: 'Message.AfterUnitBeDefeated') -> None:
        this = effect.this.CastTo(Upgrade)
        Unused(this)

        this.RemoveThreatFromSchemes(effect.targets, 5, effect)

    def remember_enemy(effect: 'Effect', message: 'Message.WhenUnitWouldBeDefeated') -> None:
        # Death-Glow leaves the enemy during its defeat interrupt.
        ability = AbilityFactory.AfterUnitBeDefeated(
            AbilityType.Response,
            message.trigger,
            flight_of_the_valkyrior,
        )
        ability.CopyFromDelayEffect(effect)
        effect.this.effect.RegisterTemp(
            ability,
            unregister_after_exec=True,
            until_event_end=message,
        )


    return [
        AbilityFactory.WhenUnitWouldBeDefeated(
            AbilityType.DelayAbility,
            HAS_DEATH_GLOW_FINDER,
            remember_enemy,
        ).SetSecondType(AbilityType.Response)
        .SetCostFunc(CostFunc.Discard("This"))
        .SetTarget(Scheme2),
    ]

