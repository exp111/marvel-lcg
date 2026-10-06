from cards.pack import *

def PsiKnifeKatana(res: 'Resources') -> List['Ability']:
    def psi_knife_flip(effect: 'Effect', message: 'Message.WhenPlayerPayingResources') -> None:
        this = effect.this.CastTo(Upgrade)
        other_face = this.card.back_faces[0]
        player = message.GetToPlayer()
        player.ChooseAbilities(
            effect,
            AbilityFactory.ForChoiceAbility(
                f"Flip to {other_face.name}",
                lambda targets:
                    Faces.FlipAllTo(targets, None, effect)
            ).SetTarget([this]),
            AbilityFactory.ForChoiceAbility(
                f"Keep {this.name}"
            ).SetTarget([this]),
            forced=False,
        )

    return [
        AbilityFactory.CanGenerateResources(
            AbilityType.HeroResource,
            res,
            ex_operation=psi_knife_flip
        ).SetCostFunc(CostFunc.Exhaust("This")),
    ]

def GetYouControlPsiKnife(player: 'Player') -> int:
    return player.GetIdentity().GetInventoryDeck().FindCardSize(CardFinder(name="Psi-Knife"))

def GetYouControlPsiKatana(player: 'Player') -> int:
    return player.GetIdentity().GetInventoryDeck().FindCardSize(CardFinder(name="Psi-Katana"))

