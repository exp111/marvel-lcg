from cards.pack import *


PROTECTION_RACKET = CardFinder(set_name="Protection Racket", card_type=MainScheme)


def GetProtectionRacketScheme(
    player: 'Player',
    effect: 'Effect',
) -> 'MainScheme|None':
    for scheme in Worlds.GetMainSchemes(effect):
        if scheme.paper.set_name == "Protection Racket" and scheme.card.GetOwner() == player:
            return scheme
    return None


def GetSchemeOwner(effect: 'Effect') -> 'Player|None':
    owner = effect.this.card.GetOwner()
    return owner if isinstance(owner, Player) else None


def IsInThisPlayArea(face: 'CardFace', effect: 'Effect') -> bool:
    owner = GetSchemeOwner(effect)
    if owner is None or face is None:
        return False
    if Minion.IsType(face):
        return face.CastTo(Minion).engaged_player == owner
    play_area = face.card.area.play_area
    if play_area is not None:
        return play_area == owner
    if Attachment.IsType(face):
        attached_to = face.CastTo(Attachment).GetBindFace()
        return attached_to is not None and IsInThisPlayArea(attached_to, effect)
    return face.GetControlBy() == owner


def PlaceThreatHere(effect: 'Effect', value: int) -> None:
    scheme = effect.this.CastTo(MainScheme)
    scheme.PlaceThreatOnSchemes([scheme], value, effect)


def ProtectionRacketLossAbilities() -> List['Ability']:
    return [
        AbilityFactory.IfThisSchemeStageIsCompletedPlayersLoseTheGame(),
        Ability(
            AbilityType.ForcedInterrupt,
            Message.WhenPlayerEliminated,
            [],
            lambda effect, message: Worlds.SetGameOver(False, effect),
        ),
    ]


def SetupProtectionRacket(
    effect: 'Effect',
    message: 'Message.WhenCardSetup',
) -> None:
    Unused(message)
    world = effect.world
    available = [
        *Worlds.GetMainSchemes(effect),
        *Worlds.MainSchemesDeck(effect).Get(),
    ]
    available = [
        face for face in available
        if MainScheme.IsType(face) and face.paper.set_name == "Protection Racket"
    ]
    selected_cards: List[Card] = []

    for player in Worlds.GetPlayers(effect):
        choices = [face for face in available if face.card not in selected_cards]
        if not choices:
            break
        if Worlds.IsExpert(effect):
            chosen = Rand.RandomChoice(choices, effect)
        else:
            chosen = player.AskChooseFace(
                choices,
                effect,
                forced=True,
                prompt="Choose your Protection Racket main scheme",
            )
        if not chosen:
            chosen = choices[0]

        selected_cards.append(chosen.card)
        chosen.card.SetOwner(player)
        if chosen.card.face.printed_target_threat is None:
            chosen.card.Flip(effect)
        active = chosen.card.face.CastTo(MainScheme)
        if active.card.area != world.area_schemes_main:
            active.PutIntoPlay(player, effect)

    unused = [face for face in available if face.card not in selected_cards]
    for face in unused:
        face.card.SetOwner(None)
    Faces.MoveAllTo(unused, world.aside_deck, effect)


def GetSetupAbilities() -> Sequence['Ability']:
    return [AbilityFactory.WhenCardSetup("This", SetupProtectionRacket)]


def SwapProtectionRacketScheme(player: 'Player', effect: 'Effect') -> bool:
    old = GetProtectionRacketScheme(player, effect)
    choices = Worlds.GetSetAsideAreaCards(effect, PROTECTION_RACKET)
    if old is None or not choices:
        return False

    new_face = Rand.RandomChoice(choices, effect)
    old_threat = old.threat
    old.card.SetOwner(None)
    Faces.MoveAllTo([old], Worlds.AsideDeck(effect), effect)

    new_face.card.SetOwner(player)
    if new_face.card.face.printed_target_threat is None:
        new_face.card.Flip(effect)
    new_scheme = new_face.card.face.CastTo(MainScheme)
    new_scheme.PutIntoPlay(player, effect)
    if old_threat:
        new_scheme.PlaceThreatOnSchemes([new_scheme], old_threat, effect)
    return True
