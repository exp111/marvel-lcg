from . import *

# Unerring Desire


def GetAbilities() -> Sequence['Ability']:
    def unerring_desire_revealed(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        this = effect.this.CastTo(Treachery)
        player = message.GetToPlayer()
        villain = Worlds.FindVillain(effect)

        give_boost_card = AbilityFactory.ForChoiceAbility(
            "Give this card to the villain as a facedown boost card",
            lambda targets: villain.GiveBoostCard(this, effect)
            if villain else None,
        ).SetTarget([villain] if villain else [])
        remove_persona = AbilityFactory.ForChoiceAbility(
            "Remove a [[PERSONA]] support you control from the game",
            lambda targets: Faces.RemoveAllFromGame(targets, effect),
        ).SetTarget(
            Support,
            trait="PERSONA",
            from_where=["YouControlCards"],
        )

        player.ChooseAbilities(
            effect,
            give_boost_card,
            remove_persona,
        )

    def unerring_desire_boost(
        effect: 'Effect',
        message: 'Message.WhenCardBecomeBoost',
    ) -> None:
        message.would_atk_message.GainOverKill(effect)

    return [
        AbilityFactory.WhenThisRevealed(
            None,
            unerring_desire_revealed,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            unerring_desire_boost,
            during_attack=True,
        ),
    ]
