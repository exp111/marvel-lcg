from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        RevealEstablishTrust(effect)
        villain = GetTyphoidVillain(effect)
        if villain:
            villain.DoSchemes(message.GetToPlayer(), effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        player = message.GetToPlayer()
        allies = player.GetControlAllies()
        ally = player.AskChooseFace(allies, effect, forced=True) if allies else None
        if ally:
            effect.this.DealDamage([ally], 3, effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            boost,
            activating_enemy=CardFinder(name="Typhoid Mary"),
        ),
    ]
