from . import *

# * Dagger


def GetAbilities() -> Sequence['Ability']:

    def cloak_is_in_play(effect: 'Effect', message: 'Message.WhenAllyWouldTakeConsequentialDamage') -> bool:
        return bool(Worlds.FindCardOnField(
            effect,
            name="Cloak",
            card_type=Ally,
        ))

    return [
        *AbilityFactory.GiveKeywordToInPlayWhenApplyThis(
            CardFinder(name="Cloak", card_type=Ally),
            apply=lambda effect, face, diff:
                face.CastTo(HasAccelerationIcon).SetIgnoreAccelerationIcon(diff, effect),
            change_on_event=OnEvent.CardInPlay(Ally),
        ),
        AbilityFactory.WhenAllyWouldTakeConsequentialDamage(
            "This",
            update_damage=-1,
            conditions=[cloak_is_in_play],
        ),
    ]
