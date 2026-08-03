from . import *

# Death Cannot Die

def GetAbilities() -> Sequence['Ability']:

    def death_cannot_die(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        if not ActivateGrimReaper(effect, player):
            Find.FindAndReveal(
                effect,
                player,
                name="Grim Reaper",
                card_type=Minion,
            )

    def death_cannot_die_boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        player = message.GetToPlayer()
        if Worlds.FindCardOnField(effect, name="Grim Reaper", card_type=Minion):
            message.AfterThisActivation(
                effect,
                lambda: ActivateGrimReaper(effect, player),
            )

    return [
        AbilityFactory.WhenThisRevealed(
            None,
            death_cannot_die,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            death_cannot_die_boost,
        ),
    ]

