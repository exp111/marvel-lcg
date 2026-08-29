from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        villain = GetTyphoidVillain(effect)
        if villain:
            Faces.GiveStatus([villain], "Tough", effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        Faces.GiveStatus([message.activating_enemy], "Tough", effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            boost,
            activating_enemy=CardFinder(name="Bloody Mary"),
        ),
    ]
