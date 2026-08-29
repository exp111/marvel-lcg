from . import *

# Deadly Sai


def GetAbilities() -> Sequence['Ability']:
    def deadly_sai_boost(
        effect: 'Effect',
        message: 'Message.WhenCardBecomeBoost',
    ) -> None:
        this = effect.this.CastTo(Attachment)
        Unused(this)
        message.activating_enemy.GainForThisActive(
            effect,
            message.being_message,
            attack=2,
        )

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(BULLSEYE),
        AbilityFactory.UnitAttackGainKeyword(
            BULLSEYE,
            piercing=True,
            lost_ranged=True,
        ),
        AbilityFactory.AfterUnitDefendAgainstAttack(
            AbilityType.HeroResponse,
            "YourHero",
            DiscardThisCard,
            attacker=BULLSEYE,
        ).SetCost(Cost("2", different_type=True)),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            deadly_sai_boost,
            during_attack=True,
        ),
    ]
