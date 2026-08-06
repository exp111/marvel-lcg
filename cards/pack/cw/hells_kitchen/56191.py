from . import *

# Resistance Fighter

def GetAbilities() -> Sequence['Ability']:

    def resistance_fighter_boost(effect: 'Effect', message: 'Message.WhenCardBecomeBoost') -> None:
        this = effect.this.CastTo(Attachment)
        Unused(this)

        player = message.GetToPlayer()
        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                "",
                lambda targets:
                    this.AttachTo2(targets[0], effect)
            ).SetTarget(player.GetEngagedMinions())
        )

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            # TODO: Enemy team choose
            Minion,
            if_cannot_gain_surge=True
        ),
        *AbilityFactory.GiveKeywordToAttached(
            Minion,
            attack=1,
            scheme=1,
            health=4,
            stalwart=1,
        ),
        AbilityFactory.WhenCardBecomeBoost(
            "This",
            resistance_fighter_boost
        ),
    ]
