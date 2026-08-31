from . import *


def GetAbilities() -> Sequence['Ability']:
    def after_attack(effect: 'Effect', message: 'Message.AfterUnitAttackEnd') -> None:
        this = effect.this.CastTo(Attachment)
        targets = [target for target in message.attacked_targets if target.IsInPlay()]
        if not targets:
            return
        target = targets[0]
        Faces.DiscardAll([this], effect)
        hammerhead = Worlds.FindCardOnField(effect, name="Hammerhead", card_type=Villain)
        if hammerhead:
            hammerhead.BasicAttack(
                [target],
                effect,
                property=AttackProperty(against_player=target.GetControlByPlayer()),
            )

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(HAMMERHEAD),
        AbilityFactory.AfterUnitAttackEnd(
            AbilityType.ForcedResponse,
            HAMMERHEAD,
            after_attack,
        ),
    ]
