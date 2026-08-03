from . import *


def GetAbilities() -> Sequence['Ability']:

    def embody_pathos_revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Attachment)
        player = message.GetToPlayer()
        scheme = Find.FindAndReveal(
            effect,
            player,
            finder=CardFinder(
                card_type=EncounterSideScheme,
                check_face_fn=lambda face: not face.IsInPlay(),
            ),
        )
        if scheme:
            printed = scheme.paper.desc.get("StartingThreat", "0")
            one_player_threat = int(eval(printed.replace("*", "*1"), {}, {}))
            scheme.SetTokens(one_player_threat, "threat", effect)
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
