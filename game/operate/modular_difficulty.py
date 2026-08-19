from . import *


class ModularDifficulty:
    @staticmethod
    def GetRecommendedValue(
        effect: 'Effect',
        *,
        per_player: bool,
    ) -> int:
        from game.operate.worlds import Worlds

        world = effect.world
        if world.rule.mode_heroic:
            value = 3
        elif Worlds.IsExpert(effect):
            value = 2
        elif world.rule.mode_skirmish:
            value = 0
        else:
            value = 1

        if per_player:
            value *= Worlds.GetPlayerNumIcon(effect)
        return value

    @staticmethod
    def MayApply(
        effect: 'Effect',
        *,
        description: Callable[[int], str],
        operation: Callable[[int], None],
        per_player: bool,
    ) -> 'Effect|None':
        from game.ability.factory import AbilityFactory
        from game.operate.worlds import Worlds

        value = ModularDifficulty.GetRecommendedValue(
            effect,
            per_player=per_player,
        )
        if value == 0:
            return None

        first_player = Worlds.GetFirstPlayer(effect)
        return first_player.MayChooseOneAbility(
            effect,
            AbilityFactory.ForChoiceAbility(
                description(value),
                lambda targets: operation(value),
            ),
        )
