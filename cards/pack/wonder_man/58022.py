from . import *

# * Swordsman

def GetAbilities() -> Sequence['Ability']:

    def swordsman_attack(effect: 'Effect', message: 'Message.WhenUnitWouldAttack') -> None:
        message.GainPiercing(effect)

    def swordsman_defend(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        this = effect.this.CastTo(Ally)
        message.being_message.DeclareDefender(this, effect)

    return [
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.NonKeyword,
            "This",
            swordsman_attack,
            is_basic_attack=True,
        ),
        Ability(
            AbilityType.HeroResponse,
            Message.WhenCardBecomeBoost,
            [
                lambda effect, message:
                    hasattr(message, "would_atk_message") and
                    message.would_atk_message.GetDefender() is None,
            ],
            swordsman_defend,
        ),
    ]
