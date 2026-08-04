from . import *

def GetAbilities() -> Sequence['Ability']:
    def discard(effect: 'Effect', message: 'Message.WhenCardRevealed|Message.WhenCardBecomeBoost') -> None:
        player = message.GetToPlayer()
        if isinstance(message, Message.WhenCardRevealed):
            faces = player.DiscardRandomHandCards(1, effect)
            if faces and HasCost.IsType(faces[0]):
                player.GetIdentity().TakeIndirectDamage(effect.this, faces[0].printed_cost.val, effect)
        else:
            player.DiscardHandCards((1, 1), effect)
    return [
        AbilityFactory.WhenThisRevealed(None, discard),
        AbilityFactory.WhenCardBecomeBoost("This", discard),
    ]
