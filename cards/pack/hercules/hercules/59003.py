from . import *


def GetAbilities() -> Sequence['Ability']:

    def embody_pathos_revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Attachment)
        player = message.GetToPlayer()
        scheme = Find.Find(
            effect,
            who_perform=player,
            finder=CardFinder(
                card_type=EncounterSideScheme,
                check_face_fn=lambda face: not face.IsInPlay(),
            ),
        )
        if not scheme:
            Faces.DiscardAll([this], effect)
            return

        # Embody Pathos treats every per-player icon on the chosen scheme as
        # one while that card is revealed, including icons in When Revealed
        # text as well as its starting threat and hinder values.
        original_player_num = scheme.player_num
        original_player_num_override = scheme.player_num_icon_override
        per_player_attributes = [
            (key, value)
            for key, value in scheme.paper.desc.items()
            if isinstance(value, str) and "*" in value
        ]

        try:
            scheme.SetPlayerNum(1)
            for key, value in per_player_attributes:
                scheme.InitPrintedValue(key, value)
            scheme.player_num_icon_override = 1
            revealed = scheme.Reveal(player, effect)
        finally:
            scheme.player_num_icon_override = original_player_num_override
            scheme.SetPlayerNum(original_player_num)
            for key, value in per_player_attributes:
                scheme.InitPrintedValue(key, value)

        if revealed is None or not scheme.IsInPlay():
            Faces.DiscardAll([this], effect)
            return

        this.AttachTo2(scheme, effect)
        this.PlaceThreatOnSchemes([scheme], 6, effect)

    def not_hercules_thwart(effect: 'Effect', message: 'Message.WhenSchemeWouldRemoveThreat') -> bool:
        return not (
            message.would_thw_message is not None and
            message.by_face.IsName("Hercules", check_all_face=True)
        )

    def complete_labor(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        Faces.AddToVictoryDisplay([effect.this], effect)

    return [
        AbilityFactory.WhenThisRevealed(None, embody_pathos_revealed),
        *AbilityFactory.GiveKeywordToAttached(
            EncounterSideScheme,
            assault=1,
        ),
        AbilityFactory.ThreatCannotBeRemovedFromWhile(
            "AttachedScheme",
            conditions=[not_hercules_thwart],
        ),
        AbilityFactory.WhenSchemeBeDefeated(
            AbilityType.Interrupt,
            "AttachedScheme",
            complete_labor,
        ),
    ]
