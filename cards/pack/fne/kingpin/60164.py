from . import *


def GetAbilities() -> Sequence['Ability']:
    def remove_grip_instead(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldAttack|Message.WhenUnitWouldThwart',
    ) -> None:
        message.SetBeInstead(effect)
        Faces.RemoveCountersOn([effect.this], 1, "grip", effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            "YourIdentity",
            conditions=[
                lambda effect, message:
                    bool(GetKingpin(effect) and GetKingpin(effect).HasTrait("MARTIAL ARTIST")),
            ],
            if_cannot_gain_surge=True,
        ),
        AbilityFactory.PlayersCannotChangeForms(
            AbilityType.NonKeyword,
            "AttachedPlayer",
            from_form=Hero,
            to_form=AlterEgo,
        ),
        AbilityFactory.WhenUnitWouldAttackOrThwart(
            AbilityType.ForcedInterrupt,
            "AttachedCharacter",
            remove_grip_instead,
        ),
    ]
