from . import *

# Starstruck

def GetAbilities() -> Sequence['Ability']:

    def starstruck(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        this = effect.this.CastTo(Event)
        hero = effect.GetInitiator().GetHero()
        this.DealDamage(effect.targets, hero.attack, effect)
        if EnergyOverpaid(effect, 1):
            Faces.GiveStatus(effect.targets, "Stunned", effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            starstruck,
        ).SetPlay().SetLabel('attack').SetTarget(Enemy),
    ]

