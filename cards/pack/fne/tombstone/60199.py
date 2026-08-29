from . import *


def GetAbilities() -> Sequence['Ability']:
    def hit_list(
        effect: 'Effect',
        message: 'Message.AfterPhaseBegin',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(EncounterSideScheme)
        identity = Worlds.GetFirstPlayer(effect).GetIdentity()
        damage_messages = identity.TakeIndirectDamage(this, 3, effect)
        defeated_allies = sum(
            1
            for damage_message in damage_messages
            if isinstance(damage_message, Message.AfterUnitDefeatedUnit)
            and Ally.IsType(damage_message.target)
        )
        if defeated_allies:
            this.RemoveThreatFromSchemes(
                [this],
                defeated_allies * Worlds.GetPlayerNumIcon(effect),
                effect,
            )

    return [
        AbilityFactory.AfterPhaseBegin(
            AbilityType.ForcedResponse,
            "Villain",
            hit_list,
        ),
    ]
