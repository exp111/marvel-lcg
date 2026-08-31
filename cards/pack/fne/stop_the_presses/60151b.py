from . import *


def GetAbilities() -> Sequence['Ability']:
    def undefended_attack(
        effect: 'Effect',
        message: 'Message.AfterUnitAttackUnit',
    ) -> None:
        player = message.attacked_you
        if player is None:
            return

        choices: List[Ability] = [
            AbilityFactory.ForChoiceAbility(
                f"Place {3 if Worlds.IsExpert(effect) else 2} threat here",
                lambda targets: effect.this.CastTo(MainScheme).PlaceThreatOnSchemes(
                    [effect.this.CastTo(MainScheme)],
                    3 if Worlds.IsExpert(effect) else 2,
                    effect,
                ),
            )
        ]
        supports = GetDailyBugleSupports(effect, player=player)
        if any(support.GetCounters("stamina") > 0 for support in supports):
            choices.append(
                AbilityFactory.ForChoiceAbility(
                    "Remove 1 stamina counter from a DAILY BUGLE support you control",
                ).SetCostFunc(
                    CostFunc.Counter(
                        Select.From(
                            faces=supports,
                            range=(1, 1),
                            not_move=True,
                            not_shuffle=True,
                        ),
                        1,
                        "stamina",
                    )
                )
            )
        player.ChooseAbilities(effect, *choices)

    def support_left_play(
        effect: 'Effect',
        message: 'Message.AfterCardsMoved',
    ) -> None:
        for face, old_area in message.face_areas.items():
            new_area = face.card.area
            if (
                DAILY_BUGLE_SUPPORT.Check(face)
                and old_area.flags.is_in_play
                and (new_area is None or not new_area.flags.is_in_play)
            ):
                Worlds.SetGameOver(False, effect)
                return

    return [
        AbilityFactory.AfterUnitAttackUnit(
            AbilityType.ForcedResponse,
            Enemy,
            "You",
            undefended_attack,
            is_undefended_attack=True,
        ),
        AbilityFactory.IfThisSchemeStageIsCompletedPlayersLoseTheGame(),
        Ability(
            AbilityType.ForcedInterrupt,
            Message.AfterCardsMoved,
            [],
            support_left_play,
        ),
    ]
