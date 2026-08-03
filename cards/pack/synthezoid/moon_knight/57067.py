from . import *

def GetAbilities() -> Sequence['Ability']:
    def exhaust(effect: 'Effect', message: 'Message.WhenCardRevealed|Message.WhenCardBecomeBoost') -> None:
        identity = message.GetToPlayer().GetIdentity()
        Faces.ExhaustAll([identity], effect)
        if isinstance(message, Message.WhenCardRevealed):
            effect.this.DealDamage([identity], 2, effect)
    return [
        AbilityFactory.WhenThisRevealed(None, exhaust),
        AbilityFactory.WhenCardBecomeBoost("This", exhaust),
    ]
