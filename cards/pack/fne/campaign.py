from . import *


CAMPAIGN_ID = "fear_no_evil"

CAMPAIGN_ENVIRONMENTS = {
    "Art Museum Heist": ("60205a", "60205b"),
    "The Getaway": ("60206a", "60206b"),
    "Protection Racket": ("60207a", "60207b"),
    "The Raft Breakout": ("60208a", "60208b"),
    "Stop the Presses!": ("60209a", "60209b"),
}

RAFT_PRISONERS = ["60144", "60145", "60146", "60147", "60148", "60149"]
DAILY_BUGLE_SUPPORTS = ["60153", "60154", "60155", "60156"]


def _log_text(key: str, effect: 'Effect') -> str:
    from game.operate.campaign_logs import CampaignLog

    return CampaignLog.GetStrInternal(key, effect).strip()


def _log_true(key: str, effect: 'Effect') -> bool:
    return _log_text(key, effect).lower() in {
        "1", "checked", "completed", "true", "yes",
    }


def GetScenarioProgress(scenario_name: str, effect: 'Effect') -> int:
    value = _log_text(f"{scenario_name} Progress", effect)
    try:
        return max(0, int(value))
    except ValueError:
        return len([item for item in value.split(";") if item])


def GetScenarioStatus(scenario_name: str, effect: 'Effect') -> str:
    status = _log_text(f"{scenario_name} Status", effect).lower()
    if status == "completed" or _log_true(f"{scenario_name} Completed", effect):
        return "Completed"
    if status == "failed" or _log_true(f"{scenario_name} Failed", effect):
        return "Failed"
    if GetScenarioProgress(scenario_name, effect) >= 3:
        return "Failed"
    return ""


def _removed_campaign_titles(effect: 'Effect') -> Set[str]:
    from game.operate.campaign_logs import CampaignLog

    keys = [
        "Allies and Persona Supports Removed from the Campaign",
        "Allies/Supports Removed from the Campaign",
    ]
    removed: Set[str] = set()
    for key in keys:
        removed.update(CampaignLog.GetListInternal(key, effect))
    return {value.strip().lstrip("* ") for value in removed if value.strip()}


def RemoveRecordedAlliesAndSupports(effect: 'Effect') -> None:
    removed = _removed_campaign_titles(effect)
    if not removed:
        return

    for player in Worlds.GetPlayers(effect):
        faces = [
            face for face in player.player_deck.Get()
            if (Ally.IsType(face) or Support.IsType(face)) and
            face.paper.is_unique and
            (face.name in removed or face.paper.card_id in removed)
        ]
        Faces.RemoveAllFromGame(faces, effect)


def ApplyExpertPersistentDamageAndHealing(effect: 'Effect') -> None:
    if not Worlds.IsExpert(effect):
        return

    for player in Worlds.GetPlayers(effect):
        value = _log_text(
            f"Player {player.player_id + 1} Remaining hit points",
            effect,
        )
        if value == "":
            continue
        try:
            remaining = int(value)
        except ValueError:
            continue

        identity = player.GetIdentity()
        identity.SetHealth(min(max(remaining, 0), identity.max_health), effect)

        def heal_identity(
            targets: Sequence['CardFace'],
            player: 'Player'=player,
            identity: 'Identity'=identity,
        ) -> None:
            player.DealEncounterCards(1, effect)
            identity.HealHealth(player.GetAlterEgo().recover, effect)

        player.MayChooseOneAbility(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Deal yourself 1 facedown encounter card to heal damage "
                "from your identity equal to its REC",
                heal_identity,
            ).SetTarget([identity], canbe_heal=True),
        )


def PutResolvedCampaignEnvironmentsIntoPlay(effect: 'Effect') -> List['Environment']:
    environments: List[Environment] = []
    for scenario_name, (completed_id, failed_id) in CAMPAIGN_ENVIRONMENTS.items():
        status = GetScenarioStatus(scenario_name, effect)
        if not status:
            continue

        card = CardFactory.GenerateCard(
            f"{completed_id},{failed_id}",
            None,
            effect.world,
        )
        if status == "Failed":
            card.face.FlipTo(effect, card_face=card.back_faces[0])
        environment = card.face.CastTo(Environment)
        environment.PutIntoPlay(Worlds.GetFirstPlayer(effect), effect)
        environments.append(environment)
    return environments


def PutTyphoidMaryCampaignAllyIntoPlay(effect: 'Effect') -> 'Ally|None':
    if not _log_true("Trust Established?", effect) or _log_true("Mary Defeated?", effect):
        return None

    first_player = Worlds.GetFirstPlayer(effect)
    players = Worlds.GetPlayers(effect)
    if not players:
        return None
    controller = first_player.AskChooseOneText(
        players,
        [str(player) for player in players],
    )
    ally = CardFactory.GenerateCard(
        "60210a,60210b",
        None,
        effect.world,
    ).face.CastTo(Ally)
    ally.PutIntoPlay(controller, effect, under_control=True)
    return ally


def _apply_interchangeable_scenario_progress(
    scenario_name: str,
    progress: int,
    effect: 'Effect',
) -> None:
    if progress <= 0:
        return

    if scenario_name in ["Art Museum Heist", "Protection Racket"]:
        threat = progress * (2 if Worlds.IsExpert(effect) else 1)
        effect.this.PlaceThreatOnSchemes(
            Worlds.GetAllMainSchemes(effect),
            threat,
            effect,
        )
        return

    if scenario_name == "The Getaway":
        first_player = Worlds.GetFirstPlayer(effect)
        tanker = SetupCards.Reveal(
            effect,
            first_player,
            name="Jackknifed Tanker Truck",
            card_type=EncounterSideScheme,
        )
        if tanker and progress >= 2:
            effect.this.PlaceThreatOnSchemes(
                [tanker],
                "2*" if Worlds.IsExpert(effect) else "1*",
                effect,
            )
        return

    if scenario_name == "The Raft Breakout":
        prisoners = Worlds.FindCardsOnField(
            effect,
            trait="PRISONER",
            card_type=Minion,
        )
        Faces.GiveStatus(prisoners, "Tough", effect)
        if progress >= 2:
            Faces.GiveFacedownBoostCards(prisoners, 1, effect)
        return

    if scenario_name == "Stop the Presses!":
        supports = Worlds.FindCardsOnField(
            effect,
            trait="DAILY BUGLE",
            card_type=Support,
        )
        Faces.RemoveCountersOn(supports, progress, "stamina", effect)


def _apply_kingpin_campaign_setup(effect: 'Effect') -> None:
    completed = sum(
        GetScenarioStatus(name, effect) == "Completed"
        for name in CAMPAIGN_ENVIRONMENTS
    )
    if completed >= 3:
        Faces.GiveStatus(
            Worlds.FindCardsOnField(effect, card_type=Minion),
            "Tough",
            effect,
        )
    if completed >= 4:
        SetupCards.Reveal(
            effect,
            Worlds.GetFirstPlayer(effect),
            name="James Wesley",
            card_type=Attachment,
        )


def CampaignSetup(scenario_name: str) -> List['Ability']:
    def remove_recorded_cards(
        effect: 'Effect',
        message: 'Message.WhenGameBeginSetup',
    ) -> None:
        Unused(message)
        RemoveRecordedAlliesAndSupports(effect)

    def after_mulligans(
        effect: 'Effect',
        message: 'Message.AfterPlayersResolveMulligans',
    ) -> None:
        Unused(message)
        ApplyExpertPersistentDamageAndHealing(effect)
        PutResolvedCampaignEnvironmentsIntoPlay(effect)
        PutTyphoidMaryCampaignAllyIntoPlay(effect)

        if scenario_name == "Kingpin":
            _apply_kingpin_campaign_setup(effect)
        else:
            _apply_interchangeable_scenario_progress(
                scenario_name,
                GetScenarioProgress(scenario_name, effect),
                effect,
            )

    return [
        AbilityFactory.WhenGameBeginSetup(
            remove_recorded_cards,
            conditions=[
                lambda effect, message:
                    Worlds.IsCampaignSelected(effect, CAMPAIGN_ID),
            ],
        ).SetName("Remove recorded campaign cards before player setup"),
        Ability(
            AbilityType.Campaign,
            Message.AfterPlayersResolveMulligans,
            [
                lambda effect, message:
                    Worlds.IsCampaignSelected(effect, CAMPAIGN_ID),
            ],
            after_mulligans,
        ).SetName(f"Fear No Evil campaign setup: {scenario_name}"),
    ]
