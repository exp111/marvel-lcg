from . import *

def GetAbilities() -> Sequence['Ability']:
    def spellcasting(effect: 'Effect', message: 'Message.WhenPlayerWouldPlayCard') -> None:
        message.CancelEffects(effect, discard_it=True)
        Faces.DiscardAll([effect.this], effect)
    return [
        AbilityFactory.WhenPlayerWouldPlayCard(
            AbilityType.ForcedInterrupt,
            "AttachedPlayer",
            None,
            spellcasting,
            conditions=[lambda effect, message: not message.be_cancel],
        )
    ]
