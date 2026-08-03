from . import *

def GetAbilities() -> Sequence['Ability']:
    def surge(effect: 'Effect', message: 'Message.WhenPlayerRevealCard') -> None:
        message.trigger.CastTo(Minion).GainSurge(1, effect)
    return [
        AbilityFactory.WhenPlayerRevealCard(
            AbilityType.ForcedInterrupt, "AnyPlayer", Minion, "All", surge
        ).LimitOncePerRound()
    ]
