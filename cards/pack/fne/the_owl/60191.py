from . import *

# Flight Serum


def GetAbilities() -> Sequence['Ability']:
    def is_attack_event(effect: 'Effect', face: 'CardFace') -> bool:
        Unused(effect)
        return Event.IsType(face) and any(
            ability.is_label_attack for ability in face.ability.abilities
        )

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            CardFinder(card_type=Enemy, non_trait="AERIAL"),
            if_cannot_gain_surge=True,
        ),
        *AbilityFactory.GiveKeywordToAttached(
            Enemy,
            trait="AERIAL",
        ),
        AbilityFactory.PlayerActionToDiscardThis(
            AbilityType.HeroAction,
        ).SetCostFunc(CostFunc.Discard(
            "YourHandCards",
            card_type=Event,
            check_effect=is_attack_event,
        )),
    ]
