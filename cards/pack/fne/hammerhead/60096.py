from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Treachery)
        player = message.GetToPlayer()
        if player.IsAlterEgo():
            this.GainSurge(1, effect)
            return
        hammerhead = Worlds.FindCardOnField(effect, name="Hammerhead", card_type=Villain)
        if not hammerhead:
            return
        identity = player.GetIdentity()
        is_stunned = identity.IsStunned()
        hammerhead.DoAttackYou(
            player,
            effect,
            property=AttackProperty(
                additional_value=2 if is_stunned else 0,
                overkill=is_stunned,
            ),
        )

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
