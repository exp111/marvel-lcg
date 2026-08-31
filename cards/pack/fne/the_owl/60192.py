from . import *

# * Mister Fish


def GetAbilities() -> Sequence['Ability']:
    def mister_fish_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(Minion)
        identities = [player.GetIdentity() for player in Worlds.GetPlayers(effect)]
        identity = Filter.One(identities, effect, fewest_remaining_hp=True)
        if identity:
            this.EngagePlayer(identity.GetControlByPlayer(), effect)

    return [
        AbilityFactory.WhenThisRevealed(
            None,
            mister_fish_revealed,
        ),
        AbilityFactory.UnitAttackGainKeyword(
            "This",
            piercing=True,
            ranged=True,
        ),
    ]
