from . import *


def GetAbilities() -> Sequence['Ability']:

    def bullseye_attacks(effect: 'Effect', player: 'Player') -> None:
        bullseye = Worlds.FindCardOnField(
            effect,
            name="Bullseye",
            card_type=Minion,
        )
        if not bullseye:
            bullseye = Find.FindAndReveal(
                effect,
                player,
                who_perform=player,
                name="Bullseye",
                card_type=Minion,
            )
        if bullseye and bullseye.IsInPlay():
            bullseye.CastTo(Minion).DoAttackYou(player, effect)

    def eye_on_the_target(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        player = message.GetToPlayer()
        removable = (
            CardFinder(card_type=Ally)
            | CardFinder(card_type=Support, trait="PERSONA")
        )
        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Remove an ally or Persona support you control from the game",
                lambda targets: Faces.RemoveAllFromGame(targets, effect),
            ).SetTarget(removable, from_where=["YouControlCards"]),
            AbilityFactory.ForChoiceAbility(
                "Bullseye attacks you",
                lambda targets: bullseye_attacks(effect, player),
            ).SetHasNoTargetEffect(),
        )

    return [
        AbilityFactory.WhenThisRevealed(None, eye_on_the_target),
    ]
