from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        effect.this.DealDamage(player.GetControlCharacters(), 1, effect)
        Faces.GiveStatus([player.GetIdentity()], "Stunned", effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        Faces.GiveStatus([message.GetToPlayer().GetIdentity()], "Stunned", effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            boost,
            activating_enemy=CardFinder(name="Typhoid Mary"),
        ),
    ]
