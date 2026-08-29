from cards.pack import *


def TombstoneAttachmentAbilities(
    after_activation: Literal["Attack", "Scheme"],
) -> List['Ability']:
    def has_highest_base_hp(effect: 'Effect', minion: 'Minion') -> bool:
        minions = Worlds.GetOnFieldMinions(effect)
        return bool(
            minions
            and minion.base_health == max(face.base_health for face in minions)
        )

    def give_tough(minion: 'CardFace', effect: 'Effect') -> None:
        Faces.GiveStatus([minion], "Tough", effect)

    def after_scheme(
        effect: 'Effect',
        message: 'Message.AfterUnitSchemeEnd',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(Attachment)
        Faces.GiveStatus(
            [Worlds.GetFirstPlayer(effect).GetIdentity()],
            "Confused",
            effect,
        )
        Faces.DiscardAll([this], effect)

    def after_attack(
        effect: 'Effect',
        message: 'Message.AfterUnitAttackEnd',
    ) -> None:
        this = effect.this.CastTo(Attachment)
        Faces.GiveStatus(message.attacked_targets, "Stunned", effect)
        Faces.DiscardAll([this], effect)

    attach_ability = AbilityFactory.AttachToFaceWhenPutIntoPlay(
            CardFinder(
                card_type=Minion,
                check_effect_fn=has_highest_base_hp,
            ),
            if_cannot_gain_surge=True,
            when_attach_operation=give_tough,
        )
    # Beetle only needs the printed kind of target.  The "highest base hit
    # points" clause determines which legal minion this attachment chooses
    # when it is revealed; Beetle's own instruction attaches it to Beetle.
    attach_ability._attachment_target_rule = CardFinder(card_type=Minion)
    abilities = [attach_ability]
    if after_activation == "Scheme":
        abilities.append(
            AbilityFactory.AfterUnitSchemeEnd(
                AbilityType.ForcedResponse,
                "AttachedMinion",
                after_scheme,
            )
        )
    else:
        abilities.append(
            AbilityFactory.AfterUnitAttackEnd(
                AbilityType.ForcedResponse,
                "AttachedMinion",
                after_attack,
            )
        )
    return abilities
