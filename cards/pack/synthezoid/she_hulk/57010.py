from . import *

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        faces = player.GetControlCharacters(CardFinder(canbe_exhaust=True))
        if faces:
            Faces.ExhaustAll(faces, effect)
        else:
            ThisCardGainSurge(effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        player = message.GetToPlayer()
        target = player.AskChooseFace(
            player.GetControlCharacters(CardFinder(canbe_exhaust=True)), effect
        )
        if target:
            Faces.ExhaustAll([target], effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
