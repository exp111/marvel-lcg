from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        for _ in range(GetSpeed(effect)):
            exhaust = AbilityFactory.ForChoiceAbility(
                "Exhaust a character you control",
            ).SetCostFunc(CostFunc.Exhaust("YouControlUnit"))
            player.ChooseAbilities(
                effect,
                exhaust,
                AbilityFactory.ForChoiceAbility(
                    "Take 1 indirect damage",
                    lambda targets: player.GetIdentity().TakeIndirectDamage(
                        effect.this,
                        1,
                        effect,
                    ),
                ),
            )

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
