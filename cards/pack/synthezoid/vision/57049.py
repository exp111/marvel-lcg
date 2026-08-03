from . import *

def GetAbilities() -> Sequence['Ability']:
    def mass_increase(effect: 'Effect', message: 'Message.WhenUnitWouldTakeDamage') -> None:
        message.PreventDamage("All", effect)
        Faces.GiveStatus([message.source], "Stunned", effect)
        Faces.DiscardAll([effect.this], effect)
    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(CardFinder(name="Vision", card_type=Leader)),
        AbilityFactory.WhenUnitWouldTakeDamage(
            AbilityType.ForcedInterrupt,
            CardFinder(name="Vision", card_type=Leader),
            mass_increase,
            is_from_attack=True,
            conditions=[lambda effect, message: bool(CardFinder(name="Dense").Checks(
                message.trigger.GetAttachedAttachments()
            ))],
        ),
    ]
