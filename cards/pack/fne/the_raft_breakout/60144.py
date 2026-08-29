from . import *


def GetAbilities() -> Sequence['Ability']:
    def attacks(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        this = effect.this.CastTo(Minion)
        player = message.GetAgainstPlayer()
        if not player:
            return
        top = player.player_deck.GetTop()
        if top:
            this.TuckCardUnderHere(top, effect)
        resource_types = FacesCounter.GetPrintedResourcesTypes(
            this.GetPlacedCardArea().GetAll()
        )
        if resource_types:
            message.GainATKForThisAttack(resource_types, effect)

    return [
        AbilityFactory.WhenUnitAttackYou(
            AbilityType.ForcedInterrupt,
            "This",
            attacks,
        ),
    ]
