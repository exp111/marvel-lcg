from . import *

def GetAbilities() -> Sequence['Ability']:
    def exhaust(effect: 'Effect', message: 'Message.WhenCardRevealed|Message.WhenCardBecomeBoost') -> None:
        player = message.GetToPlayer()
        faces = player.GetControlCharacters(CardFinder(canbe_exhaust=True))
        if faces:
            Faces.ExhaustAll(faces, effect)
        elif isinstance(message, Message.WhenCardRevealed):
            ThisCardGainSurge(effect)
    return [
        AbilityFactory.WhenThisRevealed(None, exhaust),
        AbilityFactory.WhenCardBecomeBoost("This", exhaust),
    ]
