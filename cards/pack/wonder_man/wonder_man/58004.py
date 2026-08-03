from . import *

# Ionic Blast

def GetAbilities() -> Sequence['Ability']:

    def ionic_blast(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        this = effect.this.CastTo(Event)
        value = 3 + (2 * EnergyOverpaid(effect, 3))
        this.DealDamage(effect.targets, value, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            ionic_blast,
        ).SetPlay().SetLabel('attack').SetTarget(Enemy),
    ]

