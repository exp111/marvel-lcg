from . import *

# Photon Beam

def GetAbilities() -> Sequence['Ability']:

    def photon_beam(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        this = effect.this.CastTo(Event)
        Unused(this)

        ironheart = effect.targets2

        def action(unit: 'Unit2'):
            Unused(unit)
            Faces.PlaceCountersOn(ironheart, 1, 'progress', effect)

        this.DealDamage(effect.targets, 4, effect, if_this_attack_defeats=action)

        Faces.PlaceCountersOn(ironheart, 1, 'progress', effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            photon_beam
        ).SetPlay().SetLabel('attack')
        .SetTarget(Enemy)
        .SetTarget2(name="Ironheart"),
    ]

