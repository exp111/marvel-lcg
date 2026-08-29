from . import *

# * Madame Web: Julia Carpenter

def GetAbilities() -> Sequence['Ability']:

    def madame_web(effect: 'Effect', message: 'Message.AfterCardEnterPlay') -> None:
        this = effect.this.CastTo(Ally)
        Unused(this)

        initiator = effect.GetInitiator()
        value = len(initiator.GetControlCards2(CardFinder2("WEB-WARRIOR")))
        faces = initiator.LookAtDeck("EncounterDeck", value, effect)
        discarded: List[CardFace] = []

        def action(targets: Sequence[CardFace]):
            Faces.DiscardAll(targets, effect)
            discarded.extend(targets)

        initiator.MayChooseOneAbility(
            effect,
            AbilityFactory.ForChoiceAbility(
                "Discard 1 card looked at this way and put the rest back in any order",
                action,
            ).SetTarget(
                faces,
                canbe_discard=True,
                by_search=True,
                not_move=True,
                display_in_target_order=True,
            )
        )

        rest = [x for x in faces if x not in discarded]
        initiator.PlaceOnTopInAnyOrder(rest, effect)


    return [
        AbilityFactory.AfterCardEnterPlay(
            AbilityType.Response,
            "This",
            madame_web
        ),
    ]
