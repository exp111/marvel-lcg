const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'public/scene.html'), 'utf8');
const read = name => JSON.parse(fs.readFileSync(path.join(root, 'data/scenarios', name + '.json'), 'utf8'));
function classes() {
    const values = new Set();
    return {contains: s => values.has(s), add: s => values.add(s), remove: s => values.delete(s),
        toggle(s, force = !values.has(s)) { if (force) values.add(s); else values.delete(s); return force; }};
}
const sets = JSON.parse(fs.readFileSync(path.join(root, 'data/sets_info.json'), 'utf8'));
const info = sets['56. Civil War'];
const synthezoid = sets['57. Synthezoid Smackdown'];
const modules = [...info.encounters, ...synthezoid.encounters, 'bomb_scare', 'masters_of_evil', 'weapon_master', 'a_nemesis'].map(name =>
    ({dataset: {name, family: ''}, classList: classes()}));
modules.at(-1).classList.add('nemesis');
const standards = ['standard', 'expert', 'standard_iii'].map(name =>
    ({dataset: {name, family: name.startsWith('standard') ? 'standard' : 'expert'}, classList: classes()}));
const schemes = info.scenarios.map(name => ({dataset: {scenario: JSON.stringify(read(name))}, classList: classes(), hidden: false}));
const elements = new Map();
const element = selector => {
    if (!elements.has(selector)) elements.set(selector, {classList: classes(), innerHTML: '', textContent: ''});
    return elements.get(selector);
};
let seed = 125;
const seededMath = Object.create(Math);
seededMath.random = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 2**32);
const context = vm.createContext({
    scenario: '', window: {}, Math: seededMath, console: {log: error => {throw Error(error);}},
    document: {
        querySelector: element,
        querySelectorAll(selector) {
            if (selector === '#split-scenarios button') return schemes;
            if (selector === '#modular-sets button') return modules;
            if (selector === '#modular-sets button:not(.nemesis)') return modules.filter(b => !b.classList.contains('nemesis'));
            if (selector === '#modular-sets .nemesis') return modules.filter(b => b.classList.contains('nemesis'));
            if (selector === '#encounter-sets button') return standards;
            return [];
        },
    },
    setStandardEncounterSetSelectionEnabled() {},
    get_name: id => id.split(',')[0],
});
function extract(start, end) { vm.runInContext(html.slice(html.indexOf(start), html.indexOf(end, html.indexOf(start))), context); }
extract('let selected_underling =', 'function setStandardEncounterSetSelectionEnabled(');
extract('function getEncounterSetFamily(', 'function toggleEncounterSetSelection(');
extract('function campaignRandomIndex(', 'function randomizeFearNoEvilCampaign(');
extract('function random_modular(', 'function SetHero(');
const selected = buttons => buttons.filter(b => b.classList.contains('click')).map(b => b.dataset.name);
const selectedSchemes = stage => schemes.filter(b => b.classList.contains('click') && JSON.parse(b.dataset.scenario).scheme_stage === stage);

// Default replaces every optional module, including nemeses, and leaves mandatory
// modules and the chosen Standard/Expert variants alone.
context.SetScenario({...read('rhino'), encounter_sets: ['standard', 'weapon_master']});
assert(element('#faction-modular-button').hidden);
modules.forEach(b => b.classList.add('click'));
standards[0].classList.remove('click'); standards[2].classList.add('click');
context.default_modular();
assert.deepEqual(selected(modules).sort(), ['bomb_scare', 'weapon_master']);
assert.deepEqual(selected(standards), ['standard_iii']);
assert(modules.find(b => b.dataset.name === 'weapon_master').classList.contains('lock'));

const draws = new Set();
const reached = new Set();
function checkFactionRandomization(leader) {
    const button = element('#faction-modular-button');
    assert(!button.hidden);
    assert.equal(button.textContent.toLowerCase(), leader.scenario_side);
    for (let n = 0; n < 30; n++) {
        context.faction_modular();
        const names = selected(modules);
        assert([3, 4].includes(names.length));
        assert(names.every(name => leader.modular_sets_random.includes(name)));
        names.forEach(name => reached.add(name));
        draws.add(names.slice().sort().join(','));
    }
    context.default_modular();
    assert.deepEqual(selected(modules).sort(), Array.from(leader.modular_sets).sort());
}
for (const leaderName of info.leaders) {
    const leader = read(leaderName);
    context.resetInterchangeableScenario();
    context.selectInterchangeableVillain(leader);
    assert.equal(context.scenario, '', 'A leader alone is not a complete UI scenario');
    const visible = schemes.filter(b => !b.hidden).map(b => JSON.parse(b.dataset.scenario));
    assert.equal(visible.length, 8);
    assert(visible.every(s => s.scenario_side === leader.scenario_side));
    assert.deepEqual(selected(modules).sort(), leader.modular_sets.slice().sort());
    checkFactionRandomization(leader);
    // Manual modules remain unrestricted and survive choosing/changing schemes.
    modules.forEach(b => b.classList.remove('click'));
    modules.find(b => b.dataset.name === 'bomb_scare').classList.add('click');
    const first = visible.filter(s => s.scheme_stage === 1);
    const second = visible.filter(s => s.scheme_stage === 2);
    context.selectInterchangeableMainScenario(first[0]);
    assert.equal(context.scenario, '', 'Both stages must be selected');
    context.selectInterchangeableMainScenario(second[0]);
    for (const choice of [...first, ...second]) {
        context.selectInterchangeableMainScenario(choice);
        context.selectInterchangeableMainScenario(choice);
        assert.equal(selectedSchemes(1).length, 1, 'Stage 1 is mutually exclusive and cannot be deselected');
        assert.equal(selectedSchemes(2).length, 1, 'Stage 2 is mutually exclusive and cannot be deselected');
        assert.equal(context.scenario.schemes.length, 2);
        assert.equal(context.scenario.schemes[choice.scheme_stage - 1], choice.schemes[0]);
        assert.deepEqual(selected(modules), ['bomb_scare']);
    }
    context.selectInterchangeableVillain(read(leaderName + '_expert'));
    assert(context.scenario.expert);
    assert.equal(context.scenario.schemes.length, 2, 'Changing difficulty preserves scheme choices');
    context.default_modular();
    assert.deepEqual(selected(modules).sort(), leader.modular_sets.slice().sort());
    checkFactionRandomization(context.scenario);
}
assert(draws.size > 4, 'The faction button performs fresh randomized draws');
assert(synthezoid.encounters.every(name => reached.has(name)), 'Civil War can draw all Synthezoid modular sets');
context.selectInterchangeableVillain(read('iron_man'));
assert.equal(context.scenario, '', 'Changing factions clears incompatible scheme choices');
assert.equal(selectedSchemes(1).length + selectedSchemes(2).length, 0);
context.selectInterchangeableMainScenario(read('guerilla_warfare'));
assert.equal(selectedSchemes(2).length, 0, 'A foreign faction scheme cannot be selected');

// Both Synthezoid leaders and difficulties share the expanded faction pools,
// while Default keeps their preconstructed modules.
for (const name of synthezoid.scenarios) {
    for (const suffix of ['', '_expert']) {
        context.resetInterchangeableScenario();
        assert(element('#faction-modular-button').hidden);
        const leader = read(name + suffix);
        context.SetScenario(leader);
        const cw = read(leader.scenario_side === 'registration' ? 'iron_man' : 'captain_america');
        assert.deepEqual(leader.modular_sets_random, cw.modular_sets_random);
        assert.equal(leader.modular_sets_random.length, 12);
        assert.deepEqual(selected(modules).sort(), leader.modular_sets.slice().sort());
        checkFactionRandomization(leader);
    }
}

context.SetScenario({...read('iron_man'), encounter_sets: ['standard', 'weapon_master']});
modules.at(-1).classList.add('click');
standards[0].classList.remove('click'); standards[2].classList.add('click');
context.faction_modular();
assert(selected(modules).includes('weapon_master'), 'Faction randomization preserves mandatory modules');
assert(!selected(modules).includes('a_nemesis'), 'Faction randomization clears optional nemeses');
assert.deepEqual(selected(standards), ['standard_iii']);

// Existing Fear No Evil assembly retains all main schemes and encounter cards.
context.resetInterchangeableScenario();
context.selectInterchangeableVillain(read('hammerhead'));
context.selectInterchangeableMainScenario(read('protection_racket'));
assert.equal(context.scenario.schemes.length, 5);
assert.equal(context.scenario.encounters.length, 15);
assert.deepEqual(Array.from(context.scenario.modular_sets), ['disasters', 'tracksuit_mafia']);
assert(element('#faction-modular-button').hidden, 'Other scenarios hide the faction button');
assert(html.indexOf('onclick="default_modular()"') < html.indexOf('onclick="faction_modular()"'));
assert(html.indexOf('onclick="faction_modular()"') < html.indexOf('onclick="random_modular()"'));
console.log('Civil War stages, preconstructed defaults, and faction modular UI checks passed');
