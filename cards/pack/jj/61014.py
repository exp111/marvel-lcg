from . import *
from .helpers import PlaceEvidence

# Stakeout
def GetAbilities():
    def stakeout(effect, message):
        effect.this.CastTo(Upgrade).AttachTo2(effect.targets[0], effect)

    def thwart(effect, message):
        message.GainThwartForThisThwart(2, effect)
        scheme = message.scheme
        source_effect = message.would_thw_message.by_effect
        effect.this.effect.RegisterTemp(
            AbilityFactory.AfterUnitDefeatedScheme(AbilityType.Temp0, None, scheme,
                lambda followup, defeated: PlaceEvidence(effect, 2),
                conditions=[lambda followup, defeated: defeated.by_effect == source_effect]
            ).NoOutOfPlayLimit(),
            unregister_after_exec=True, until_event_end=message.would_thw_message,
        )

    return [
        AbilityFactory.WhenInYourPlayTurn(AbilityType.Action, stakeout,
            conditions=[lambda effect, message: effect.this.GetBindFace() == effect.GetInitiator().GetIdentity()])
            .SetTarget(CardFinder(card_type=EncounterSideScheme, is_permanent=False)),
        AbilityFactory.WhenUnitThwartScheme(AbilityType.Interrupt, Unit2, thwart,
            which_card_be_thwart="AttachedScheme"),
    ]
