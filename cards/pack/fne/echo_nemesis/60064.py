from . import *


def GetAbilities() -> Sequence['Ability']:
    def pawn_alter_ego(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        kingpin = Worlds.FindCardOnField(
            effect,
            name="Kingpin",
            card_type=Minion,
        )
        if kingpin:
            kingpin.CastTo(Minion).DoSchemes(message.GetToPlayer(), effect)
        else:
            ThisCardGainSurge(effect)

    def pawn_hero(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        attack = message.GetToPlayer().GetHero().attack
        effect.this.DealDamage(effect.targets, attack, effect)

    return [
        AbilityFactory.WhenThisRevealed(
            "Alter-Ego",
            pawn_alter_ego,
        ),
        AbilityFactory.WhenThisRevealed(
            "Hero",
            pawn_hero,
        ).SetTarget(Hero),
    ]
