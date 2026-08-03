from . import *

def GetAbilities() -> Sequence['Ability']:
    def remove_threat(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        this.RemoveThreatFromSchemes([this], 3, effect)
    return [
        AbilityFactory.PlayersCannotRemoveThreatFrom(
            "AnyPlayer",
            "This",
            conditions=[lambda effect, message: Hero.IsType(message.by_effect.this) or Ally.IsType(message.by_effect.this)],
        ),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.AlterEgoAction, remove_threat
        ).SetCostFunc(CostFunc.Exhaust("YourIdentity")),
    ]
