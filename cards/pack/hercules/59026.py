from . import *


def GetAbilities() -> Sequence['Ability']:

    def can_resolve_ancient_rivalry(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> bool:
        player = effect.GetInitiator()
        if player.discard_pile.FindCard(
            card_type=Upgrade,
            card_class="IdentitySpecific",
        ):
            return True
        return bool(Worlds.FindCardsOnField(
            effect,
            finder=CardFinder(names=["Hercules", "Thor"], canbe_ready=True),
        ))

    def ancient_rivalry(effect: 'Effect', message: 'Message.WhenPlayerInTurn') -> None:
        player = effect.GetInitiator()
        upgrade = Search.PlayerCard(
            effect,
            player,
            include_player_deck=False,
            include_discard_pile=True,
            card_type=Upgrade,
            card_class="IdentitySpecific",
        )
        if upgrade:
            Faces.MoveAllTo([upgrade], player.hand_cards, effect)

        characters = Worlds.FindCardsOnField(
            effect,
            finder=CardFinder(names=["Hercules", "Thor"], canbe_ready=True),
        )
        Faces.ReadyAll(characters, effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            ancient_rivalry,
            conditions=[can_resolve_ancient_rivalry],
        ).SetPlay().SetTarget("TeamUp"),
    ]
