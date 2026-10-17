from . import *

# Cottonmouth
def GetAbilities():
    def repeat_attacks(effect, message):
        this = effect.this.CastTo(Minion)
        targets = list(message.attacked_targets)
        for _ in range(2):
            living = [target for target in targets if target.IsInPlay() and not target.IsDefeated()]
            if not this.IsInPlay() or not living:
                break
            this.BasicAttack(living, effect, property=AttackProperty(resolve_separately=True))

    def boost(effect, message):
        for identity in Worlds.GetPlayersIdentities(effect, CardFinder(name="Luke Cage")):
            identity.GetControlByPlayer().DealEncounterCard(effect.this, effect)
            break

    return [
        AbilityFactory.AfterUnitAttackEnd(AbilityType.ForcedResponse, "This", repeat_attacks)
            .LimitOncePerPhase(),
        AbilityFactory.WhenCardBecomeBoost("This", boost),
    ]
