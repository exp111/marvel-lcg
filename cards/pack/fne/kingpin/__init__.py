from cards.pack import *


KINGPIN = CardFinder(name="Kingpin", card_type=Villain)
UNDERLING = CardFinder(trait="UNDERLING", card_type=Minion)


def GetKingpin(effect: 'Effect') -> 'Villain|None':
    face = Worlds.FindCardOnField(effect, KINGPIN)
    return face.CastTo(Villain) if face else None


def GetNemesisMinion(player: 'Player') -> 'Minion|None':
    faces = CardFinder(
        card_type=Minion,
        is_nemesis=player,
    ).Checks(player.set_aside_nemesis_sets.Get())
    return faces[0].CastTo(Minion) if faces else None


def RevealUnderlingNotInPlay(
    player: 'Player',
    effect: 'Effect',
    *,
    encounter_deck_only: bool=False,
) -> 'Minion|None':
    minion = Search.SearchForCard(
        effect,
        player,
        include_encounter_deck=True,
        include_encounter_discard_pile=not encounter_deck_only,
        include_set_aside=not encounter_deck_only,
        finder=UNDERLING,
    )
    if minion:
        minion.Reveal(player, effect)
        return minion.CastTo(Minion)
    return None


def RevealSetupNemesis(player: 'Player', effect: 'Effect') -> None:
    minion = GetNemesisMinion(player)
    if not minion:
        return
    if any(
        character != minion and character.IsName(minion.name)
        for character in Worlds.GetOnFieldCharacters(effect)
    ):
        Faces.RemoveAllFromGame([minion], effect)
        RevealUnderlingNotInPlay(player, effect)
        return
    minion.Reveal(player, effect)


def FindAndRevealNemesisForEndgame(player: 'Player', effect: 'Effect') -> bool:
    entered_play = False

    def entered() -> None:
        nonlocal entered_play
        entered_play = True

    minion = Find.Find(
        effect,
        who_perform=player,
        finder=CardFinder(card_type=Minion, is_nemesis=player),
    )
    if minion:
        minion.Reveal(player, effect, if_entered_play=entered)
    return entered_play


def KingpinStageOneAbilities() -> List['Ability']:
    def scheme_instead(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldAttack',
    ) -> None:
        villain = effect.this.CastTo(Villain)
        player = message.GetAgainstPlayer()
        message.SetBeInstead(effect)
        if player:
            villain.DoSchemes(player, effect)

    return [
        AbilityFactory.UnitCannotTakeDamageWhile(
            AbilityType.NonKeyword,
            "This",
        ),
        *AbilityFactory.UnitCannotHaveUpgradeAttached("This"),
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.ForcedInterrupt,
            "This",
            scheme_instead,
        ),
    ]


def KingpinStageTwoAbilities(*, expert: bool) -> List['Ability']:
    def activation(
        effect: 'Effect',
        message: 'Message.WhenEnemyActivateAgainstYou',
    ) -> None:
        player = message.GetToPlayer()
        if not player.GetEngagedMinions():
            message.GiveAdditionalBoostCardForThisActivation(1, effect)
            if expert and isinstance(message.would_message, Message.WhenUnitWouldAttack):
                message.would_message.GainOverKill(effect)

    return [
        AbilityFactory.WhenEnemyActivateAgainstYou(
            AbilityType.ForcedInterrupt,
            "This",
            activation,
        ),
    ]


def PublicSupportAfterMinionDefeated() -> 'Ability':
    def place_support(
        effect: 'Effect',
        message: 'Message.AfterUnitBeDefeated',
    ) -> None:
        Unused(message)
        Faces.PlaceCountersOn([effect.this], 1, "support", effect)

    return AbilityFactory.AfterUnitBeDefeated(
        AbilityType.ForcedResponse,
        Minion,
        place_support,
    )


def AttachToKingpinOrSurge(*, retaliate: int|None=None) -> List['Ability']:
    abilities: List[Ability] = [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            KINGPIN,
            conditions=[
                lambda effect, message:
                    bool(GetKingpin(effect) and GetKingpin(effect).HasTrait("MARTIAL ARTIST")),
            ],
            if_cannot_gain_surge=True,
        ),
    ]
    if retaliate is not None:
        abilities += AbilityFactory.GiveKeywordToAttached(
            KINGPIN,
            retaliate=retaliate,
        )
    return abilities
