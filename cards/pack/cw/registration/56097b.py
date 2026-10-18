from . import *

# Hunting Rebel Heroes

def GetAbilities() -> Sequence['Ability']:
    def register_response(effect: 'Effect', message: 'Message.WhenCardEnterPlay') -> None:
        # Keep reveal tracking on this scheme instance, not in the cached
        # ability definitions shared by different games.
        affected_heroes: Dict['CardFace', List['Hero']] = {}

        def remember_heroes(effect: 'Effect', message: 'Message.AfterCardGainTrait') -> None:
            heroes = affected_heroes.setdefault(message.by_effect.this, [])
            hero = message.trigger.CastTo(Hero)
            if hero not in heroes:
                heroes.append(hero)

        def hunting_rebel_heroes(effect: 'Effect', message: 'Message.AfterCardRevealedEnd') -> None:
            heroes = affected_heroes.pop(message.trigger, [])
            effect.this.DealDamage([hero for hero in heroes if hero.IsInPlay()], 2, effect)

        effect.this.effect.RegisterTemp(
            # Remember recipients during the reveal, then resolve one response
            # after that card has finished revealing.
            AbilityFactory.AfterCardGainTrait(
                AbilityType.NonKeyword,
                Hero,
                "UNREGISTERED",
                remember_heroes,
                conditions=[lambda effect, message:
                    effect.this != message.by_effect.this and
                    message.by_effect.this.card.state.is_revealing],
            ),
            AbilityFactory.AfterPlayerRevealCard(
                AbilityType.ForcedResponse,
                "AnyPlayer",
                None,
                hunting_rebel_heroes,
                conditions=[lambda effect, message: bool(affected_heroes.get(message.trigger))],
            ),
            unregister_after_exec=False,
            until_this_leave_play=True,
        )


    return [
        *AbilityFactory.GiveKeywordToInPlayWhenApplyThis(
            Hero,
            trait="UNREGISTERED",
            change_on_event=OnEvent.CardInPlay(Hero)
        ),
        AbilityFactory.WhenCardEnterPlay(
            AbilityType.Temp0,
            "This",
            register_response,
            include_face_changes=True,
        ),
    ]

