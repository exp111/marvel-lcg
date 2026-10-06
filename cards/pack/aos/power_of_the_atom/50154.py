from . import *

# Runaway Nuclear Reaction

def GetAbilities() -> Sequence['Ability']:
    radioactive_man = CardFinder(name="Radioactive Man")

    def runaway_nuclear_reaction(effect: 'Effect', message: 'Message.AfterFaceDealDamage') -> None:
        this = effect.this.CastTo(EncounterSideScheme)
        Unused(this)

        # Overkill can also deal damage to the villain in the same damage event.
        value = sum(damage.deal_damage for damage in message.dealt_damage_messages
                    if radioactive_man.Check(damage.who_took_damage))
        this.PlaceThreatOnSchemes([this], value, effect)

        if this.threat >= 10:
            units = Worlds.GetOnFieldCharacters(effect)
            this.DealDamage(units, 10, effect)
            Faces.DiscardAll([this], effect)

    return [
        AbilityFactory.AfterFaceDealDamage(
            AbilityType.ForcedResponse,
            None,
            radioactive_man,
            runaway_nuclear_reaction,
            conditions=[lambda effect, message: message.by_effect != effect],
        ),
    ]

