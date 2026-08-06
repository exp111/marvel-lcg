from . import *

def _flip_mass_form(effect: 'Effect', message: 'Message.AfterResolveVillainPhaseStep') -> None:
    leader = effect.this.CastTo(Leader)
    forms = CardFinder(names=["Dense", "Intangible"]).Checks(leader.GetAttachedAttachments())
    if forms:
        forms[0].card.Flip(effect)

def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Leader)
        Utility.DealEachPlayerEncounterCard(effect)
        Utility.CannotTakeDamageThisPhase(this, effect)

    return [
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.AfterResolveVillainPhaseStep(
            AbilityType.ForcedResponse, 1, _flip_mass_form
        ),
    ]
