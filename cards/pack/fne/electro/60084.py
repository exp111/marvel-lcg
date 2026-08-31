from . import *


def GetAbilities() -> Sequence['Ability']:
    def revealed(effect: 'Effect', message: 'Message.WhenCardRevealed') -> None:
        this = effect.this.CastTo(Treachery)
        player = message.GetToPlayer()
        energy_cards = [
            face for face in player.hand_cards.Get()
            if FacesCounter.GetPrintedResources([face]).HasColorPrinted("Y")
        ]
        if not energy_cards:
            this.GainSurge(1, effect)
            return
        for face in list(energy_cards):
            if face not in player.hand_cards.Get():
                continue
            player.ChooseAbilities(
                effect,
                AbilityFactory.ForChoiceAbility(
                    f"Discard {face.name}",
                    lambda targets: Faces.DiscardAll(targets, effect),
                ).SetTarget([face]),
                AbilityFactory.ForChoiceAbility(
                    "Stun a character you control",
                    lambda targets: Faces.GiveStatus(targets, "Stunned", effect),
                ).SetTarget(
                    player.GetControlCharacters(CardFinder(canbe_stunned=True)),
                ),
            )

    return [AbilityFactory.WhenThisRevealed(None, revealed)]
