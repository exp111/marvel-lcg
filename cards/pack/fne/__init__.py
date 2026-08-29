from cards.pack import *


SENSE_CARD_IDS = ["60002", "60003", "60004", "60005", "60006"]


def GetSenseDeck(player: 'Player') -> 'Deck':
    return player.additional_deck


def GetSenseAttachmentTargets(face: 'CardFace', effect: 'Effect') -> List['CardFace']:
    if face.paper.card_id in ["60002", "60003"]:
        targets: List[CardFace] = [
            *Worlds.GetOnFieldEnemies(effect),
            *Worlds.GetOnFieldSchemes(effect),
        ]
    elif face.paper.card_id in ["60004", "60005"]:
        targets = list(Worlds.GetOnFieldEnemies(effect))
    elif face.paper.card_id == "60006":
        targets = list(Worlds.GetOnFieldSchemes(effect))
    else:
        targets = []
    return [target for target in targets if face.CastTo(Upgrade).CanAttachTo(target)]


def GetPlayableSenseCards(player: 'Player', effect: 'Effect') -> List['Upgrade']:
    deck = GetSenseDeck(player)
    return [
        face.CastTo(Upgrade)
        for face in deck.Get()
        if face.HasTrait("SENSE") and GetSenseAttachmentTargets(face, effect)
    ]


def ChooseAndPlaySenseUpgrade(
    player: 'Player',
    effect: 'Effect',
    *,
    top_only: bool=False,
    ignore_resources_cost: bool=False,
    force_choice: bool=False,
) -> List['CardFace']:
    deck = GetSenseDeck(player)
    if top_only:
        top = deck.GetTop()
        faces = [top] if top and GetSenseAttachmentTargets(top, effect) else []
    else:
        faces = GetPlayableSenseCards(player, effect)
    if not faces:
        return []
    face = player.AskChooseFace(
        faces,
        effect,
        forced=top_only or force_choice,
        peek=True,
        not_move=True,
    )
    if not face:
        return []
    return player.PlayCardsLikeInTurn(
        [face],
        effect,
        ignore_resources_cost=ignore_resources_cost,
        forced=ignore_resources_cost,
        if_not_play_discard_it=False,
    )


def SetupSenseDeck(effect: 'Effect', message: 'Message.WhenPlayerSelectHero') -> None:
    from game.message import Message

    player = effect.GetInitiator()
    deck = GetSenseDeck(player)
    deck.face_up_override = True
    senses = CardFinder(trait="SENSE", card_type=Upgrade).Checks(
        player.set_aside_deck.Get()
    )
    Faces.MoveAllTo(senses, deck, effect)
    Message.WhenDeckCreated_Text(deck)
    deck.Shuffle(effect)
    Faces.FlipAllTo(deck.Get(), True, effect)


def SenseDeckRuleAbilities() -> List['Ability']:
    def put_on_bottom_of_sense_deck(
        effect: 'Effect',
        message: 'Message.WhenCardWouldMoveToArea',
    ) -> None:
        player = message.trigger.GetOwnerPlayer()
        message.ChangeToBottomOfDeck(GetSenseDeck(player), effect)

    def controlled_by_you(
        effect: 'Effect',
        message: 'Message.WhenCardWouldMoveToArea',
    ) -> bool:
        return message.trigger.GetOwnerPlayer() == effect.GetInitiator()

    def not_already_moving_to_sense_deck(
        effect: 'Effect',
        message: 'Message.WhenCardWouldMoveToArea',
    ) -> bool:
        return message.into_area != GetSenseDeck(effect.GetInitiator())

    return [
        AbilityFactory.WhenCardWouldMoveToArea(
            AbilityType.ForcedInterrupt,
            CardFinder(trait="SENSE", card_type=Upgrade),
            put_on_bottom_of_sense_deck,
            from_play=True,
            conditions=[
                controlled_by_you,
                not_already_moving_to_sense_deck,
            ],
        ),
    ]
