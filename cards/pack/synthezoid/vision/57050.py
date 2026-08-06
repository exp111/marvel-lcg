from . import *

def GetAbilities() -> Sequence['Ability']:
    def change_form(effect: 'Effect', desired: str) -> None:
        leader = effect.this.GetBindFace().CastTo(Leader)
        forms = CardFinder(names=["Dense", "Intangible"]).Checks(leader.GetAttachedAttachments())
        if forms and forms[0].paper.name != desired:
            forms[0].card.Flip(effect)
            Faces.DiscardAll([effect.this], effect)
    return [
        AbilityFactory.AttachToFaceWhenPutIntoPlay(CardFinder(name="Vision", card_type=Leader)),
        AbilityFactory.WhenUnitWouldScheme(
            AbilityType.ForcedInterrupt,
            "AttachedCharacter",
            lambda effect, message: change_form(effect, "Intangible"),
        ),
        AbilityFactory.WhenUnitWouldAttack(
            AbilityType.ForcedInterrupt,
            "AttachedCharacter",
            lambda effect, message: change_form(effect, "Dense"),
        ),
    ]
