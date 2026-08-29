from . import *


def GetAbilities() -> Sequence['Ability']:

    def raising_hell(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        damage_per_upgrade = 3 if effect.GetInitiator().GetIdentity().HasTrait("AERIAL") else 2
        this = effect.this.CastTo(Event)
        for enemy in Worlds.GetOnFieldEnemies(effect):
            damage = damage_per_upgrade * len(enemy.GetAttachedUpgrades())
            if damage:
                this.DealDamage(
                    [enemy],
                    damage,
                    effect,
                    property=AttackProperty(),
                )

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            raising_hell,
        ).SetPlay().SetLabel("attack").SetHasNoTargetEffect(),
    ]
