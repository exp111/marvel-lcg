const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Element {
    constructor(id = '') {
        this.id = id;
        this.disabled = false;
        this.innerHTML = '';
        this.dataset = { id: String(id) };
        this.childNodes = [];
        this.listeners = {};
        this.attributes = {};
        const classes = new Set();
        this.classList = {
            add: (...names) => names.forEach(name => classes.add(name)),
            remove: (...names) => names.forEach(name => classes.delete(name)),
            contains: name => classes.has(name),
            toggle: name => classes.has(name) ? classes.delete(name) : classes.add(name),
        };
    }
    replaceChildren() { this.childNodes = []; }
    appendChild(child) { this.childNodes.push(child); }
    addEventListener(name, callback) { this.listeners[name] = callback; }
    setAttribute(name, value) { this.attributes[name] = value; }
    getAttribute(name) { return this.attributes[name] || ''; }
    querySelector() { return null; }
    click() { this.listeners.click({ target: this, stopPropagation() {}, preventDefault() {} }); }
}
function createClient(compiledDirectory, fixtures) {
const elements = new Map();
function element(id) {
    if (!elements.has(id)) elements.set(id, new Element(id));
    return elements.get(id);
}
const context = vm.createContext({
    assert, structuredClone, element, window: {}, console: { log() {} },
    HTMLButtonElement: Element,
    fixtures,
    document: {
        getElementById: element, createElement: () => new Element(),
        querySelector: () => null, querySelectorAll: () => [],
    },
});
vm.runInContext(`
    const Lib = {
        array: { occurrence: (items, item) => items.filter(x => x === item).length,
                 hasDuplicates: items => new Set(items).size !== items.length },
        object: { isEmpty: value => Object.keys(value).length === 0 },
        game: { cleanResText: text => text },
    };
    const Game = { is_lost_connect: false };
    const UI = { event_name: 'WhenPlayerChooseAbility', is_in_play_turn: false,
        prompt: { resetPromptText() {}, setTempPromptText() {} }, selectCountClear() {}, update() {} };
    const Music = { playClickCardSound() {} };
    const Replay = { prepared_replay: true };
    const FullSearchPresentation = { dismissIfActive: () => false, isActive: () => false };
    const Setting = { player_id: 0, auto_effect_black_list: [] };
    const ClientPreferences = { showDeckDuringFullSearch: () => false };
    const ButtonSetting = { auto_target: true, auto_target_forced: true, auto_activate: true, is_replay: false };
    const ClassName = { auto_activate: 'auto_activate' };
    const HoverCard = { whenCardActive() {} };
    const Command = { setLastClickCard: () => false };
    const Cards = { records: new Map(), getDiv: element, getSpanText: id => 'Card ' + id,
        getCard(id) { return this.records.get(id); } };
    const submissions = [];
    class XMLHttpRequest {
        open() {}
        setRequestHeader() {}
        send(text) {
            submissions.push(JSON.parse(text));
            this.readyState = 4;
            this.status = 200;
            this.onreadystatechange();
        }
    }
`, context);
// Use the actual auto-target and per-card activation settings, as well as
// selection, confirmation and cancellation. Stub only rendering and transport.
for (const name of ['data', 'select', 'btn_ok', 'auto_targeting', 'auto_activate', 'effect', 'buttons']) {
    const source = fs.readFileSync(path.join(compiledDirectory, name + '.js'), 'utf8')
        .replace(/^import .*\r?\n/gm, '').replace(/^export /gm, '');
    vm.runInContext(source, context, { filename: name + '.js' });
}
return context;
}
module.exports = createClient;

if (require.main === module) {
const context = createClient(process.argv[2], JSON.parse(fs.readFileSync(process.argv[3], 'utf8')));
vm.runInContext(`
    Effect.updateHighLight = () => {};
    Button.clean = () => {};
    Button.disablePause = () => {};
    function prepare(fixture, autoTarget, autoActivate) {
        submissions.length = 0;
        Effect.reset();
        SelectStep.reset();
        ButtonSetting.auto_target = autoTarget;
        ButtonSetting.auto_activate = autoActivate;
        AutoActivate.config.clear();
        Cards.records = new Map(fixture.cards.map(card => [card.id, card]));
        for (const card of fixture.cards) {
            const div = element(card.id);
            div.parentElement = element('table');
            div.classList.add(ClassName.auto_activate);
            AutoActivate.config.add(card.card_id);
        }
        Effect.response_json_ask = new AskOptionPayload(fixture.ask);
        Effect.setOptions();
    }

    // The former descriptor allowed automatic submission of a singleton
    // optional discard. Reproduce the report's three commonly lost upgrades
    // without changing the running engine or the real client implementation.
    const formerlyAutomatic = [];
    for (const fixture of fixtures) {
        const option = JSON.parse(fixture.ask.options_json)[0];
        if (option.automatic_targets.length === 0) continue;
        prepare(fixture, true, true);
        Effect.response_json_ask.options[0].automatic_submit = true;
        Effect.update();
        assert.equal(submissions.length, 1);
        assert.equal(submissions[0].id, option.id);
        formerlyAutomatic.push(Cards.getCard(option.bind_id).card_id);
    }
    assert.equal(JSON.stringify(formerlyAutomatic), JSON.stringify(['51010', '51012', '51013']));

    for (const fixture of fixtures) {
        for (const autoTarget of [false, true]) {
            for (const autoActivate of [false, true]) {
                for (const accept of [false, true]) {
                    prepare(fixture, autoTarget, autoActivate);
                    Effect.update();
                    assert.equal(submissions.length, 0, 'An optional discard must never submit on opening');
                    const [discard, cancel] = Effect.response_json_ask.options;
                    assert.equal(cancel.name, 'Cancel');
                    const cancelId = cancel.choice_id || cancel.id;
                    if (accept) {
                        if (Effect.select_effect_obj.id === -1) {
                            Effect.options_button_div.childNodes[0].click();
                        }
                        if (Effect.select_effect_obj.selected_targets.length < discard.target_num_range[0]) {
                            for (const target of discard.all_legal_targets.slice(0, discard.target_num_range[0])) {
                                if (!Effect.select_effect_obj.selected_targets.includes(target)) {
                                    Effect.onCardClick(element(target), false);
                                }
                            }
                        }
                        assert.equal(submissions.length, 0, 'The discard still requires explicit confirmation');
                        Button.doBtnOk();
                        assert.equal(submissions.length, 1);
                        assert.equal(submissions[0].id, discard.choice_id || discard.id);
                        assert.equal(submissions[0].targets.length, discard.target_num_range[0]);
                    } else {
                        Button.doBtnCancel();
                        assert.equal(submissions.length, 1);
                        assert.equal(submissions[0].id, cancelId);
                        assert.equal(submissions[0].targets.length, 0);
                    }
                }
            }
        }
    }
`, context, { filename: 'shuri-optional-discard-checks' });
}
