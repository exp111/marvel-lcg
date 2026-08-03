from . import *

# Disarming Defense

def GetAbilities() -> Sequence['Ability']:

    def disarming_defense(effect: 'Effect', message: 'Message.WhenUnitWouldDefend') -> None:
        this = effect.this.CastTo(Event)
        Unused(this)

        initiator = effect.GetInitiator()
        message.GainDEFForThisAttack(+2, effect)

        def discard_attachment():
            Players.DiscardHeroActionAttachment(
                initiator,
                [message.attacker],
                effect,
                may=False,
            )

        message.IfYouTakeNoDamage(discard_attachment)


    return [
        AbilityFactory.WhenUnitDefendAgainstAttack(
            AbilityType.Interrupt,
            "YourHero",
            disarming_defense,
        ).SetPlay().SetLabel('defense'),
    ]
