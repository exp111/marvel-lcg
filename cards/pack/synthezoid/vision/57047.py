from . import *

def GetAbilities() -> Sequence['Ability']:
    def flip_mass_form(effect: 'Effect', message: 'Message.AfterUnitAttackEnd') -> None:
        leader = Worlds.GetEnemyLeader(effect)
        if leader:
            forms = CardFinder(names=["Dense", "Intangible"]).Checks(
                leader.GetAttachedAttachments()
            )
            if forms:
                forms[0].card.Flip(effect)

    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(
            CardFinder(name="Vision", card_type=Leader)
        ),
        *AbilityFactory.GiveKeywordToAttached(Leader, stalwart=1),
        AbilityFactory.AfterUnitMakeBasicAttack(
            AbilityType.HeroResponse,
            "You",
            flip_mass_form,
            against_who="AttachedEnemy",
        ).SetCost(Cost("YR")).SetCostFunc(CostFunc.Discard("This")),
        AbilityFactory.WhenCardBecomeBoost("This", RevealThisCard),
    ]
