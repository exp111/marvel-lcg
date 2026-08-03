from . import *

def _damage_changed_hero(effect: 'Effect', message: 'Message.AfterUnitChangeForm') -> None:
    effect.this.DealDamage([message.trigger], 1, effect)

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Leader)
        Utility.DealEachPlayerEncounterCard(effect)
        Utility.CannotTakeDamageThisPhase(this, effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.AfterUnitChangeForm(
            AbilityType.ForcedResponse, None, _damage_changed_hero, to_form=Hero
        ),
    ]
