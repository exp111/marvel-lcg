from . import *

def GetAbilities() -> Sequence['Ability']:
    def discard(effect: 'Effect', message: 'Message.WhenCardRevealed|Message.WhenCardBecomeBoost') -> None:
        player = message.GetToPlayer()
        faces = player.DiscardRandomHandCards(1, effect)
        if isinstance(message, Message.WhenCardRevealed) and faces and HasCost.IsType(faces[0]):
            player.GetIdentity().TakeIndirectDamage(effect.this, faces[0].printed_cost.val, effect)
    return [
        AbilityFactory.WhenThisRevealed(None, discard),
        AbilityFactory.WhenCardBecomeBoost("This", discard),
    ]
