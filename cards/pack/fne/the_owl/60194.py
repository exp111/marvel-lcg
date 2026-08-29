from . import *

# Swoop Down


def GetAbilities() -> Sequence['Ability']:
    AERIAL_ENEMY = CardFinder(trait="AERIAL", card_type=Enemy)

    def with_aerial_bonus(
        effect: 'Effect',
        operation: Callable[[], Any],
    ) -> None:
        this = effect.this.CastTo(Treachery)
        temp_effects = this.effect.RegisterTemp(
            AbilityFactory.WhenUnitWouldAttack(
                AbilityType.Temp0,
                AERIAL_ENEMY,
                lambda bonus_effect, attack_message:
                    attack_message.GainATKForThisAttack(2, effect),
            ),
            AbilityFactory.WhenUnitWouldScheme(
                AbilityType.Temp0,
                AERIAL_ENEMY,
                lambda bonus_effect, scheme_message:
                    scheme_message.GainSCHForThisScheme(2, effect),
            ),
            unregister_after_exec=False,
        )
        operation()
        Effects.UnRegister(temp_effects)

    def swoop_down_alter_ego(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        player = message.GetToPlayer()

        def activate() -> None:
            villain = Worlds.FindVillain(effect)
            if villain:
                villain.DoSchemes(player, effect)
            Worlds.Enemies.EngagedMinionSchemes(effect, player)

        with_aerial_bonus(effect, activate)

    def swoop_down_hero(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        player = message.GetToPlayer()
        with_aerial_bonus(
            effect,
            lambda: Worlds.Enemies.VillainAndEngagedMinionsAttackYou(
                effect,
                player,
            ),
        )

    return [
        AbilityFactory.WhenThisRevealed(
            "Alter-Ego",
            swoop_down_alter_ego,
        ),
        AbilityFactory.WhenThisRevealed(
            "Hero",
            swoop_down_hero,
        ),
    ]
