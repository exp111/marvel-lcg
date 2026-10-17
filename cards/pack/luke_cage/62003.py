from . import *

# Harlem's Hero
def GetAbilities():
    def harlem(effect,message):
        identity=effect.GetInitiator().GetIdentity()
        Faces.GiveStatus([identity],"Tough",effect)
        for _ in range(identity.tough):
            effect.GetInitiator().ChooseAbilities(effect,AbilityFactory.ForChoiceAbility("Ready a character you control",
                lambda targets: Faces.ReadyAll(targets,effect)).SetTarget("YouControlCharacter",canbe_ready=True))
    return [AbilityFactory.WhenInYourPlayTurn(AbilityType.HeroAction,harlem).SetPlay()]
