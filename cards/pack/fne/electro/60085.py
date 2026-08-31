from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Treachery)
        player = message.GetToPlayer()
        discarded = player.DiscardDeckTopCards(len(player.GetControlCards()), effect)
        for face in discarded:
            if not FacesCounter.GetPrintedResources([face]).HasColorPrinted("Y"):
                continue
            charge = GetElectricCharge(effect)
            player.ChooseAbilities(
                effect,
                AbilityFactory.ForChoiceAbility(
                    "Take 1 indirect damage",
                    lambda targets: player.GetIdentity().TakeIndirectDamage(this, 1, effect),
                ),
                AbilityFactory.ForChoiceAbility(
                    "Place 1 charge counter on Electric Charge",
                    lambda targets, target=charge:
                        Faces.PlaceCountersOn([target], 1, 'charge', effect) if target else None,
                ),
            )

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
