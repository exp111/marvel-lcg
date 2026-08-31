from cards.pack import *


ART_ATTACHMENT = CardFinder(trait="ART", card_type=Attachment)


def GetArtAttachmentsOnIdentities(effect: 'Effect') -> List['Attachment']:
    attachments: List[Attachment] = []
    for player in Worlds.GetPlayers(effect):
        attachments.extend(
            ART_ATTACHMENT.Checks(player.GetIdentity().GetInventoryDeck().Get())
        )
    return attachments


def MoveArtFromIdentityToVillain(effect: 'Effect', player: 'Player',
                                 *,
                                 identity: 'Identity|None'=None) -> bool:
    villain = Worlds.FindVillain(effect)
    attachments = (
        ART_ATTACHMENT.Checks(identity.GetInventoryDeck().Get())
        if identity else GetArtAttachmentsOnIdentities(effect)
    )
    if not villain or not attachments:
        return False
    attachment = player.AskChooseFace(attachments, effect, forced=True)
    return bool(attachment and attachment.AttachTo2(villain, effect))


def ArtAttachmentAbilities(status: 'CardFace.STATUS|None'=None,
                           *,
                           stalwart: bool=False,
                           resource: 'Resources.RBYG') -> List['Ability']:
    resource_text = {
        "B": "a [mental] resource",
        "G": "a [wild] resource",
        "R": "a [physical] resource",
        "Y": "an [energy] resource",
    }[resource]

    def after_art_attaches(
        effect: 'Effect',
        message: 'Message.AfterCardAttachTo',
    ) -> None:
        if status:
            Faces.GiveStatus([message.to_face], status, effect)

    def attach_to_your_hero(
        effect: 'Effect',
        message: 'Message.WhenPlayerInTurn',
    ) -> None:
        Unused(message)
        this = effect.this.CastTo(Attachment)
        this.AttachTo2(effect.GetInitiator().GetHero(), effect)

    abilities: List[Ability] = [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(Villain),
        *AbilityFactory.GiveKeywordToAttached(
            "Character",
            scheme=1,
            thwart=1,
            stalwart=1 if stalwart else None,
        ),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            attach_to_your_hero,
        ).SetCost(Cost(resource)).SetName(
            f"Spend {resource_text} → attach this card to your hero"
        ),
        AbilityFactory.WhenInYourPlayTurn(
            AbilityType.HeroAction,
            attach_to_your_hero,
        ).SetCostFunc(CostFunc.Exhaust("YourHero")).SetName(
            "Exhaust your hero → attach this card to your hero"
        ),
    ]
    if status:
        abilities.insert(
            2,
            AbilityFactory.AfterCardAttachTo(
                AbilityType.ForcedResponse,
                "This",
                "Character",
                after_art_attaches,
            ),
        )
    return abilities
