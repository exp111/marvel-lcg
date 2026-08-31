from . import *

# Raise the Stakes


def GetAbilities() -> Sequence['Ability']:
    def raise_the_stakes(
        effect: 'Effect',
        message: 'Message.WhenUnitWouldAttack',
    ) -> None:
        this = effect.this.CastTo(Attachment)
        message.GiveAdditionalBoostCardForThisActivation(1, effect)

        message.IfThisAttackDefeats(
            Friend,
            lambda target: Faces.RemoveAllFromGame([target, this], effect),
            effect,
        )

        def shuffle_if_still_in_play() -> None:
            if this.IsInPlay():
                Faces.ShuffleAllTo([this], "EncounterDeck", effect)

        RunAt.AfterEventEnd(effect, message, shuffle_if_still_in_play)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(BULLSEYE),
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.ForcedInterrupt,
            BULLSEYE,
            raise_the_stakes,
        ),
    ]
