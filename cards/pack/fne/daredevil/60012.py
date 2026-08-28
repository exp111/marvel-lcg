from . import *


def GetAbilities() -> Sequence['Ability']:

    def not_daredevil_or_matt_murdock(
        effect: 'Effect',
        message: 'Message.WhenSchemeWouldRemoveThreat',
    ) -> bool:
        return not message.by_face.IsName("Daredevil", check_all_face=True)

    def focus_the_senses(effect: 'Effect', message: 'Message.WhenSchemeBeDefeated') -> None:
        player = message.GetDefeatingPlayer()

        senses_in_play = [
            face.CastTo(Upgrade)
            for face in Worlds.GetOnFieldCards(effect)
            if Upgrade.IsType(face)
            and face.HasTrait("SENSE")
            and face.GetOwner() == player
        ]
        movable = [
            sense
            for sense in senses_in_play
            if any(
                target != sense.GetBindFace()
                for target in GetSenseAttachmentTargets(sense, effect)
            )
        ]
        selected_in_play = player.AskChooseFaces(
            movable,
            (0, "All"),
            effect,
            prompt="Choose Sense upgrades to move",
            forced=False,
            not_move=True,
        )
        for sense in selected_in_play:
            targets = [
                target
                for target in GetSenseAttachmentTargets(sense, effect)
                if target != sense.GetBindFace()
            ]
            target = player.AskChooseFace(
                targets,
                effect,
                prompt=f"Choose a new attachment for {sense.name}",
            )
            if target:
                sense.CastTo(Upgrade).AttachTo2(target, effect)

        senses_in_deck = GetPlayableSenseCards(player, effect)
        selected_in_deck = player.AskChooseFaces(
            senses_in_deck,
            (0, "All"),
            effect,
            prompt="Choose Sense upgrades to put into play",
            forced=False,
            peek=True,
            not_move=True,
            not_shuffle=True,
        )
        for sense in selected_in_deck:
            sense.PutIntoPlay(player, effect)

    return [
        AbilityFactory.ThreatCannotBeRemovedFromWhile(
            "This",
            conditions=[not_daredevil_or_matt_murdock],
        ),
        AbilityFactory.WhenSchemeBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            focus_the_senses,
            has_defeating_player=True,
        ),
    ]
