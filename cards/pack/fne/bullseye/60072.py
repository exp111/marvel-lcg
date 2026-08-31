from . import *

# * Lady Bullseye


def GetAbilities() -> Sequence['Ability']:
    def prepare_lady_bullseye_interrupt(
        effect: 'Effect',
        attack_message: 'Message.WhenUnitWouldAttack',
    ) -> None:
        this = effect.this.CastTo(Minion)

        def give_additional_boost_card(
            boost_effect: 'Effect',
            boost_message: 'Message.WhenBoostCardWouldTurnedFaceUp',
        ) -> None:
            Unused(boost_effect)
            this.GiveFacedownBoostCardsInternal(1, effect, attack_message)

        this.effect.RegisterTemp(
            AbilityFactory.WhenBoostCardWouldTurnedFaceUp(
                AbilityType.ForcedInterrupt,
                give_additional_boost_card,
                while_attack=True,
                boost_for_card=this,
                conditions=[
                    lambda boost_effect, boost_message:
                        boost_message.would_atk_message == attack_message and
                        attack_message.GetDefender() is None,
                ],
            ),
            unregister_after_exec=True,
            until_event_end=attack_message,
        )

    return [
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.NonKeyword,
            "This",
            prepare_lady_bullseye_interrupt,
        ),
    ]
