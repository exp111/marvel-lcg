from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        faces = player.set_aside_nemesis_sets.Get()
        if not faces:
            effect.this.CastTo(Treachery).GainSurge(1, effect)
            return
        if not Rand.RandomChoice(faces, effect).Reveal(player, effect):
            effect.this.CastTo(Treachery).GainSurge(1, effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        player = message.GetToPlayer()
        faces = player.set_aside_nemesis_sets.Get()
        if not faces:
            return
        message.activating_enemy.GiveBoostCard(
            Rand.RandomChoice(faces, effect),
            effect,
            message.would_message,
        )

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
