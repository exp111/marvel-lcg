from . import *


def GetAbilities() -> Sequence['Ability']:

    def bullseye_revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        this = effect.this.CastTo(Minion)
        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Discard a Persona support you control",
                lambda targets: Faces.DiscardAll(targets, effect),
            ).SetTarget(
                CardFinder(card_type=Support, trait="PERSONA", canbe_discard=True),
                from_where=["YouControlCards"],
            ),
            AbilityFactory.ForChoiceAbility(
                "Bullseye attacks you",
                lambda targets: this.DoAttackYou(player, effect),
            ).SetHasNoTargetEffect(),
        )

    return [
        AbilityFactory.WhenThisRevealed(None, bullseye_revealed),
    ]
