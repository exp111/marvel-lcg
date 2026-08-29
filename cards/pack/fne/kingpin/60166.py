from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        Faces.GiveStatus([message.GetToPlayer().GetIdentity()], "Stunned", effect)

    def after_attack(
        effect: 'Effect',
        message: 'Message.AfterUnitAttackEnd',
    ) -> None:
        heroes = CardFinder(card_type=Hero).Checks(message.damaged_targets)
        if heroes and Faces.GiveStatus(heroes, "Stunned", effect) > 0:
            Faces.DiscardAll([effect.this], effect)

    def boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        identity = message.GetToPlayer().GetIdentity()
        if identity.IsStunned():
            identity.TakeDamage(effect.this, 1, effect)
        else:
            Faces.GiveStatus([identity], "Stunned", effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(KINGPIN),
        AbilityFactory.WhenThisRevealed(None, revealed),
        AbilityFactory.AfterUnitAttackEnd(
            AbilityType.ForcedResponse,
            KINGPIN,
            after_attack,
            damaged_who=Hero,
        ),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
