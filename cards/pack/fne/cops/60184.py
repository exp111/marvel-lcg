from . import *

# Wanted


def GetAbilities() -> Sequence['Ability']:
    def wanted(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(Obligation)
        player = effect.GetInitiator()
        minion = Worlds.DiscardEncounterCardsUntil(
            effect,
            trait="POLICE",
            card_type=Minion,
        )
        if minion:
            minion.PutIntoPlay(player, effect)
        Faces.DiscardAll([this], effect)

    return [
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            wanted,
            conditions=[
                lambda effect, message:
                    effect.this.CastTo(Obligation).GetGaveToPlayer() == effect.GetInitiator(),
            ],
        ),
    ]
