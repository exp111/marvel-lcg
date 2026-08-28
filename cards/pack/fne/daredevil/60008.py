from . import *


def GetAbilities() -> Sequence['Ability']:

    def cross_examination(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        target = effect.targets[0]
        attached_upgrades = len(target.GetAttachedUpgrades())
        bonus = 0
        if attached_upgrades:
            bonus = effect.GetInitiator().AskChooseOneText(
                list(range(attached_upgrades + 1)),
                [
                    f"Deal {value} additional damage"
                    for value in range(attached_upgrades + 1)
                ],
            )
        damage = 3 + bonus
        effect.this.CastTo(Event).DealDamage(
            [target],
            damage,
            effect,
            property=AttackProperty(),
        )

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            cross_examination,
        ).SetPlay().SetLabel("attack").SetTarget(Enemy),
    ]
