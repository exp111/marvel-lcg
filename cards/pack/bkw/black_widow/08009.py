from . import *

# * Synth-Suit

def GetAbilities() -> Sequence['Ability']:

    def synth_suit(effect: 'Effect', message: 'Message.AfterEffectResolved') -> None:
        this = effect.this.CastTo(Upgrade)
        Unused(this)

        Faces.ReadyAll(effect.targets, effect)


    return [
        *AbilityFactory.GiveKeywordToAttached(
            CardFinder(name="Black Widow"),
            defense=1,
        ),
        AbilityFactory.AfterPlayerResolveAbility(
            AbilityType.HeroResponse,
            "You",
            CardFinder2("PREPARATION"),
            synth_suit,
            control_by_you=True,
            conditions=[
                lambda effect, message: not message.effect.ability.flags.is_temp,
            ],
        ).SetCostFunc(CostFunc.Exhaust("This"))
        .SetTarget(name="Black Widow", canbe_ready=True),
    ]

