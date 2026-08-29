from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        RevealEstablishTrust(effect)
        villain = GetTyphoidVillain(effect)
        if villain:
            villain.DoAttackYou(message.GetToPlayer(), effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        effect.this.DealDamage([message.GetToPlayer().GetIdentity()], 2, effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            boost,
            activating_enemy=CardFinder(name="Bloody Mary"),
        ),
    ]
