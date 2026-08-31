from . import *

# Tug of War


def GetAbilities() -> Sequence['Ability']:
    def tug_of_war(
        effect: 'Effect',
        message: 'Message.WhenCardRevealed',
    ) -> None:
        this = effect.this.CastTo(Treachery)
        player = message.GetToPlayer()
        villain = Worlds.FindVillain(effect)
        art_on_villain = (
            villain.GetInventoryDeck().FindCards(ART_ATTACHMENT)
            if villain else []
        )

        def recover_art(targets: Sequence['CardFace'], resources: 'Resources') -> None:
            Unused(resources)
            if targets:
                targets[0].CastTo(Attachment).AttachTo2(player.GetIdentity(), effect)

        def do_not_pay(targets: Sequence['CardFace']) -> None:
            Unused(targets)
            MoveArtFromIdentityToVillain(effect, player)
            ThisCardGainSurge(effect)

        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbilityWithCost(
                Cost("RRR"),
                "Spend 3 physical resources to recover an ART attachment",
                recover_art,
            ).SetTarget(art_on_villain),
            AbilityFactory.ForChoiceAbility(
                "Do not spend 3 physical resources",
                do_not_pay,
            ),
        )

    return [
        AbilityFactory.WhenThisRevealed(
            None,
            tug_of_war,
        ),
    ]
