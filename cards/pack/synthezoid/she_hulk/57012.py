from . import *

def GetAbilities() -> Sequence['Ability']:
    def remove_threat(effect: 'Effect', message: 'Message.AfterUnitChangeForm') -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        this.RemoveThreatFromSchemes([this], 3, effect)
    return [
        AbilityFactory.PlayersCannotRemoveThreatFrom(
            "AnyPlayer",
            "This",
            conditions=[lambda effect, message: Hero.IsType(message.by_effect.this) or Ally.IsType(message.by_effect.this)],
        ),
        AbilityFactory.AfterUnitChangeForm(
            AbilityType.AlterEgoResponse,
            "You",
            remove_threat,
            to_form=AlterEgo,
        ).SetCostFunc(CostFunc.Exhaust("YourIdentity")),
    ]
