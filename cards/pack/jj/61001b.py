from . import *

# Jessica Jones
def GetAbilities():
    def incognito(effect, message):
        player = effect.GetInitiator()
        player.GetIdentity().ChangeToForm(Hero, effect)
        player.GetIdentity().effect.RegisterTemp(
            AbilityFactory.PlayersCannotChangeForms(AbilityType.Temp0, "You", to_form=AlterEgo),
            unregister_after_exec=False, until_phase_end=True,
        )
    return [
        AbilityFactory.SetupPutIntoPlay(["61002"]),
        AbilityFactory.WhenInYourPlayTurn(AbilityType.Action, incognito).SetName("Incognito Mode"),
    ]
