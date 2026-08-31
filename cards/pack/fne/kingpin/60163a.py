from . import *


def GetAbilities() -> Sequence['Ability']:
    def raise_support(
        effect: 'Effect',
        message: 'Message.WhenPhaseBegin',
    ) -> None:
        Unused(message)
        villain = GetKingpin(effect)
        scheme = Worlds.FindMainScheme(effect)
        if villain:
            villain.card.Flip(effect)
        if scheme:
            scheme.Advance("2A", effect)
        if effect.this.card.face == effect.this:
            effect.this.card.Flip(effect)

    return [
        PublicSupportAfterMinionDefeated(),
        AbilityFactory.WhenVillainPhaseBegin(
            AbilityType.ForcedInterrupt,
            raise_support,
            conditions=[
                lambda effect, message:
                    effect.this.GetCounters("support") >= (
                        2 * Worlds.GetPlayerNumIcon(effect) + 2
                    ),
            ],
        ),
    ]
