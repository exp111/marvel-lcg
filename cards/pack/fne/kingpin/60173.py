from . import *


def GetAbilities() -> Sequence['Ability']:
    def defeated(
        effect: 'Effect',
        message: 'Message.WhenSchemeBeDefeated',
    ) -> None:
        player = message.GetDefeatingPlayer()
        scheme = Worlds.FindCardOnField(
            effect,
            CardFinder(card_type=SideScheme, is_nemesis=player),
        )
        if scheme:
            effect.this.PlaceThreatOnSchemes([scheme], 3, effect)
        else:
            Find.FindAndReveal(
                effect,
                player,
                who_perform=player,
                finder=CardFinder(card_type=SideScheme, is_nemesis=player),
            )

    return [
        AbilityFactory.WhenSchemeBeDefeated(
            AbilityType.WhenDefeated,
            "This",
            defeated,
            has_defeating_player=True,
        ),
    ]
