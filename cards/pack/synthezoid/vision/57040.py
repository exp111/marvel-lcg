from . import *

def _flip_mass_form(effect: 'Effect', message: 'Message.AfterResolveVillainPhaseStep') -> None:
    leader = effect.this.CastTo(Leader)
    forms = CardFinder(name=["Dense", "Intangible"]).Checks(leader.GetAttachedAttachments())
    if forms:
        forms[0].card.Flip(effect)

def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        this = effect.this.CastTo(Leader)
        SetupCards.AttachTo(
            effect,
            attach_to=this,
            name="Dense",
            card_type=Attachment,
        )

    return [
        AbilityFactory.WhenCardSetup("This", setup),
        AbilityFactory.AfterResolveVillainPhaseStep(
            AbilityType.ForcedResponse, 1, _flip_mass_form
        ),
    ]
