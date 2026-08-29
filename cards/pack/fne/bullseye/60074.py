from . import *

# Everything Is a Weapon


def GetAbilities() -> Sequence['Ability']:
    def everything_is_a_weapon_alter_ego(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        this = effect.this.CastTo(Treachery)
        message.GetToPlayer().GetIdentity().TakeIndirectDamage(this, 2, effect)

    def everything_is_a_weapon_hero(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        this = effect.this.CastTo(Treachery)
        player = message.GetToPlayer()
        bullseye = Worlds.FindCardOnField(effect, BULLSEYE)

        activate_bullseye = AbilityFactory.ForChoiceAbility(
            "Bullseye activates against you",
            lambda targets: bullseye.DoActivate(player, effect)
            if bullseye else None,
        ).SetTarget([bullseye] if bullseye else [])
        remove_ally = AbilityFactory.ForChoiceAbility(
            "Remove an ally you control from the game",
            lambda targets: Faces.RemoveAllFromGame(targets, effect),
        ).SetTarget("YourAlly")

        player.ChooseAbilities(
            effect,
            activate_bullseye,
            remove_ally,
        )

    def everything_is_a_weapon_boost(
        effect: 'Effect',
        message: 'Message.WhenCardBecomeBoost',
    ) -> None:
        message.GiveActivatingEnemyAdditionalBoostCard(1, effect)
        message.would_atk_message.GainPiercing(effect)

    return [
        AbilityFactory.WhenThisRevealed(
            "Alter-Ego",
            everything_is_a_weapon_alter_ego,
        ),
        AbilityFactory.WhenThisRevealed(
            "Hero",
            everything_is_a_weapon_hero,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            everything_is_a_weapon_boost,
            during_attack=True,
            activating_enemy=BULLSEYE,
        ),
    ]
