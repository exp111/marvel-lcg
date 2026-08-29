from . import *

# Incessant Pursuit


def GetAbilities() -> Sequence['Ability']:
    def incessant_pursuit(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldAttack',
    ) -> None:
        this = effect.this.CastTo(Attachment)
        attached_ally = this.GetBindFace()
        if not Ally.IsType(attached_ally):
            return

        message.ReplaceTarget(attached_ally)
        message.GainOverKill(effect)
        message.IfThisAttackDefeats(
            attached_ally,
            lambda target: Faces.RemoveAllFromGame([target], effect),
            effect,
        )

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            Ally,
            without_another_copy=True,
            if_cannot_gain_surge=True,
        ),
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.ForcedInterrupt,
            Villain,
            incessant_pursuit,
            against_player="AttachedPlayer",
        ),
    ]
