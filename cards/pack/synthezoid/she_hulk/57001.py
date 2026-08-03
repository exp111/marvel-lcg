from . import *

def _damage_changed_hero(effect: 'Effect', message: 'Message.AfterUnitChangeForm') -> None:
    effect.this.DealDamage([message.trigger], 1, effect)

def GetAbilities() -> Sequence['Ability']:
    def setup(effect: 'Effect', message: 'Message.WhenCardSetup') -> None:
        this = effect.this.CastTo(Leader)
        SetupCards.AttachTo(effect, attach_to=this, name="Superhuman Strength", card_type=Attachment)

    return [
        AbilityFactory.WhenCardSetup("This", setup),
        AbilityFactory.AfterUnitChangeForm(
            AbilityType.ForcedResponse, None, _damage_changed_hero, to_form=Hero
        ),
    ]
