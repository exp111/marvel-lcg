from cards.pack import *


BULLSEYE = CardFinder(name="Bullseye", card_type=Villain)


def BullseyeActivationAbilities() -> List['Ability']:
    def bullseye_activates(
        effect: 'Effect',
        message: 'Message.WhenEnemyActivateAgainstYou',
    ) -> None:
        this = effect.this.CastTo(EncounterVillain)

        this.effect.RegisterTemp(
            AbilityFactory.WhenBoostIconsWouldBeCount(
                AbilityType.Temp0,
                lambda boost_effect, boost_message:
                    boost_message.UpdateBoostIcon(+1, effect),
            ),
            unregister_after_exec=False,
            until_event_end=message,
        )
        if isinstance(message.would_message, Message.WhenUnitWouldAttack):
            message.would_message.GainRanged(effect)

    return [
        AbilityFactory.WhenEnemyActivateAgainstYou(
            AbilityType.ForcedInterrupt,
            "This",
            bullseye_activates,
        ),
    ]
