from . import *


def GetAbilities() -> Sequence['Ability']:
    def swap(effect: 'Effect', player: 'Player') -> None:
        SwapProtectionRacketScheme(player, effect)

    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        swap(effect, message.GetToPlayer())

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        swap(effect, message.GetToPlayer())

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
