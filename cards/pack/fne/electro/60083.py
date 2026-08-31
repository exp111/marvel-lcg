from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Treachery)
        player = message.GetToPlayer()
        charge = GetElectricCharge(effect)
        damage = 3 if charge and charge.GetCounters('charge') > 0 else 1
        for character in player.GetControlCharacters():
            player.ChooseAbilities(
                effect,
                AbilityFactory.ForChoiceAbility(
                    f"Exhaust {character.name}",
                    lambda targets: Faces.ExhaustAll(targets, effect),
                ).SetTarget([character], canbe_exhaust=True),
                AbilityFactory.ForChoiceAbility(
                    f"Deal {damage} damage to {character.name}",
                    lambda targets, value=damage: this.DealDamage(targets, value, effect),
                ).SetTarget([character]),
            )
        if charge and charge.GetCounters('charge') > 0:
            Faces.RemoveCountersOn([charge], 1, 'charge', effect)

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
