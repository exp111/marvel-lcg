from . import *

# Art Museum Heist 1B


def GetAbilities() -> Sequence['Ability']:
    def escalation_from_stolen_art(effect: 'Effect') -> int:
        villain = Worlds.FindVillain(effect)
        art_count = 0
        if villain:
            art_count = villain.GetInventoryDeck().FindCardSize(ART_ATTACHMENT)
        return (1 + art_count) * Worlds.GetPlayerNumIcon(effect)

    def enemy_steals_art(
        effect: 'Effect',
        message: 'Message.AfterUnitAttackUnit',
    ) -> None:
        player = message.attacked.GetControlByPlayer()
        MoveArtFromIdentityToVillain(
            effect,
            player,
            identity=message.attacked.CastTo(Identity),
        )

    return [
        AbilityFactory.WhenCalcThisSchemeEscalation(
            escalation_from_stolen_art,
        ),
        AbilityFactory.AfterUnitAttackUnit(
            AbilityType.ForcedResponse,
            Enemy,
            Identity,
            enemy_steals_art,
            is_undefended_attack=True,
        ),
    ]
