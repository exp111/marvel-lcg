from . import *


def GetAbilities() -> Sequence['Ability']:
    def the_rez(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        identity = effect.GetInitiator().GetIdentity()
        tucked = identity.GetPlacedCardArea().GetAll()
        if not tucked:
            return
        value = max(face.CastTo(HasCost).printed_cost.val for face in tucked)
        identity.HealthUnits([identity], value, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.AlterEgoAction,
            the_rez,
            conditions=[
                lambda effect, message:
                    effect.GetInitiator().GetIdentity()
                    .GetPlacedCardArea().GetSize() > 0,
            ],
        ).SetCostFunc(CostFunc.Exhaust("This")),
    ]
