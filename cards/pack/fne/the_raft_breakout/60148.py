from . import *


def GetAbilities() -> Sequence['Ability']:
    def attacks(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        player = message.GetAgainstPlayer()
        scheme = Worlds.FindMainScheme(effect, against_player=player)
        if not player:
            return
        choices: List[Ability] = []
        if scheme:
            choices.append(
                AbilityFactory.ForChoiceAbility(
                    "Place 1 threat on the main scheme",
                    lambda targets: scheme.PlaceThreatOnSchemes(
                        [scheme],
                        1,
                        effect,
                    ),
                )
            )
        choices.append(
            AbilityFactory.ForChoiceAbility(
                "Proxima Midnight gets +2 ATK for this attack",
                lambda targets: message.GainATKForThisAttack(2, effect),
            )
        )
        player.ChooseAbilities(effect, *choices)

    return [
        AbilityFactory.WhenUnitAttackYou(
            AbilityType.ForcedInterrupt,
            "This",
            attacks,
        ),
    ]
