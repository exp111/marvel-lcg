from cards.pack import *


PURPLE_MAN = CardFinder(name="Purple Man", card_type=Villain)
INFLUENCED_MINION = CardFinder(trait="INFLUENCED", card_type=Minion)


def PurpleManVillainAbilities(*, villainous: bool=False, patrol: bool=False) -> List['Ability']:
    def purple_boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        player = message.GetToPlayer()
        boost_card = message.trigger
        message.AfterThisActivation(
            effect,
            lambda: player.DealEncounterCard(boost_card, effect),
        )

    return [
        *AbilityFactory.GiveKeywordToInPlayWhenApplyThis(
            INFLUENCED_MINION,
            guard=1,
            villainous=1 if villainous else None,
            patrol=1 if patrol else None,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            CardFinder(set_name="Purple Man"),
            purple_boost,
        ),
    ]


def InfluencedMinionDefeated(
    operation: Callable[['Effect', 'Message.WhenUnitBeDefeated'], None],
) -> 'Ability':
    return AbilityFactory.WhenUnitBeDefeated(
        AbilityType.WhenDefeated,
        "This",
        operation,
    )


def PurpleCommandAbility(
    name: str,
    operation: Callable[['Effect', 'Player'], None],
    *,
    conditions: ConditionsType[Message.WhenPlayerInTurn]=[],
) -> List['Ability']:
    def command(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        operation(effect, effect.GetInitiator())

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.ForcedAction,
            command,
            conditions=conditions,
        ).SetCostFunc(CostFunc.Exhaust("This"))
        .SetCostFunc(CostFunc.Counter("This", 1, "command"))
        .SetName(name),
    ]
