const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../public/scene.html'), 'utf8');
const checkboxTag = html.match(/<input\b[^>]*id="remove_standard_set_restriction"[^>]*>/)[0];
assert(!/\bchecked(?:\s|=|>)/.test(checkboxTag), 'Restriction removal defaults off');
const cacheIds = html.match(/cache_ids\s*=\s*(\[[\s\S]*?\])/)[1];
assert(!cacheIds.includes('remove_standard_set_restriction'), 'Opt-out is not carried to new setup pages');

const checkbox = { checked: false };
const row = {
    id: 'encounter-sets', buttons: [],
    querySelectorAll(selector) {
        const family = selector.match(/data-family="(.*?)"/)[1];
        return this.buttons.filter(button => button.dataset.family === family);
    },
};
function button(name, selected, parent = row, locked = false) {
    const family = name.startsWith('standard') ? 'standard' : name.startsWith('expert') ? 'expert' : '';
    const classes = new Set([...(selected ? ['click'] : []), ...(family ? ['required-family'] : []), ...(locked ? ['lock'] : [])]);
    const result = {
        dataset: {name, family}, parentElement: parent, disabled: false,
        classList: {
            contains: value => classes.has(value),
            add: value => classes.add(value),
            remove: value => classes.delete(value),
            toggle: value => classes.has(value) ? classes.delete(value) : classes.add(value),
        },
    };
    parent.buttons.push(result);
    return result;
}
const standard = button('standard', true);
const standardII = button('standard_ii', false);
const standardIII = button('standard_iii', false);
const expert = button('expert', true);
const expertII = button('expert_ii', false);
const modular = button('prelates', true, {id: 'modular-sets', buttons: []}, true);
const context = vm.createContext({
    scenario: {encounter_sets: ['prelates', 'standard', 'expert']},
    document: {
        getElementById: id => id === 'encounter-sets' ? row : checkbox,
        querySelectorAll: selector => row.querySelectorAll(selector),
    },
});
vm.runInContext(html.slice(html.indexOf('function setStandardEncounterSetSelectionEnabled('),
                          html.indexOf('var last_current_package')), context);
vm.runInContext(html.slice(html.indexOf('function getEncounterSetFamily('), html.indexOf('async function createSets(')), context);
const toggle = context.toggleEncounterSetSelection;
const selected = b => b.classList.contains('click');

toggle(standard); toggle(expert);
assert(selected(standard) && selected(expert), 'Required families stay selected by default');
toggle(standardIII); toggle(expertII);
assert(!selected(standard) && selected(standardIII) && !selected(expert) && selected(expertII), 'Variants remain replaceable');
toggle(standardIII); toggle(expertII);
assert(selected(standardIII) && selected(expertII), 'Alternate variants are protected too');

checkbox.checked = true;
toggle(standardIII); toggle(expertII);
assert(row.buttons.every(b => !selected(b)), 'Opt-out permits removing both families entirely');
toggle(modular);
assert(selected(modular), 'Required modular sets stay locked');

// Every combination of the five difficulty packs is independently selectable.
for (let mask = 0; mask < 1 << row.buttons.length; mask++) {
    row.buttons.forEach((b, index) => { if (mask & (1 << index)) toggle(b); });
    row.buttons.forEach((b, index) => assert.equal(selected(b), Boolean(mask & (1 << index))));
    row.buttons.filter(selected).forEach(toggle);
    assert(row.buttons.every(b => !selected(b)), 'Each pack can also be independently deselected');
}

// Keep the chosen alternate Expert set when restoring a missing Standard set.
toggle(expertII);
checkbox.checked = false;
context.applyStandardSetRestriction();
assert(selected(standard) && !selected(standardIII));
assert(selected(expertII) && !selected(expert));
toggle(standard);
assert(selected(standard), 'Turning off the option restores protection');

checkbox.checked = true;
toggle(standard); toggle(expertII);
checkbox.checked = false;
context.applyStandardSetRestriction();
assert(selected(standard) && selected(expert), 'Both missing families restore on turning off');

// Turning the override off restores one per family, even for optional families.
context.scenario = {encounter_sets: ['prelates', 'standard']};
checkbox.checked = true;
toggle(standardII); toggle(standardIII); toggle(expertII);
assert(row.buttons.every(selected));
checkbox.checked = false;
context.applyStandardSetRestriction();
assert.deepEqual(row.buttons.filter(selected).map(b => b.dataset.name), ['standard_iii', 'expert_ii']);

// Scenario exclusions apply by default, and are also lifted by this override.
context.scenario = {encounter_sets: ['expert'], standard_sets: false};
context.applyStandardSetRestriction();
assert([standard, standardII, standardIII].every(b => b.disabled && !selected(b)));
checkbox.checked = true;
context.applyStandardSetRestriction();
assert(row.buttons.every(b => !b.disabled));
toggle(standard); toggle(standardII); toggle(standardIII);
assert([standard, standardII, standardIII].every(selected));
// Changing to another restricted scenario must respect the checked override too.
context.setStandardEncounterSetSelectionEnabled(false);
assert([standard, standardII, standardIII].every(b => !b.disabled && selected(b)));
checkbox.checked = false;
context.applyStandardSetRestriction();
assert([standard, standardII, standardIII].every(b => b.disabled && !selected(b)));
assert(selected(expertII), 'Restoring a scenario exclusion retains its selected Expert variant');
console.log('Encounter-set restriction UI checks passed');
