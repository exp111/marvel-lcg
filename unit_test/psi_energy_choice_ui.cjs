const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Exercise the compiled client with real engine descriptors. Only rendering,
// audio and transport are stubbed; prompt selection and submission are real.
class Element {
    constructor() {
        this.disabled = false;
        this.innerHTML = '';
        this.dataset = {};
        this.childNodes = [];
        this.listeners = {};
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
    click() {
        this.listeners.click({ target: this, stopPropagation() {}, preventDefault() {} });
    }
}
const elements = new Map();
function element(id) {
    if (!elements.has(id)) {
        const value = new Element();
        value.dataset.id = String(id);
        elements.set(id, value);
    }
    return elements.get(id);
}
const context = vm.createContext({
    assert, structuredClone, element, window: {}, console: { log() {} },
    HTMLButtonElement: Element,
    fixtures: JSON.parse(fs.readFileSync(process.argv[3], 'utf8')),
    document: {
        getElementById: element,
        createElement: () => new Element(),
        querySelector: () => null,
        querySelectorAll: () => [],
    },
});
vm.runInContext(`
    const Lib = {
        array: { occurrence: (items, item) => items.filter(x => x === item).length },
        game: { cleanResText: text => text },
    };
    const Game = { is_lost_connect: false };
    const UI = { event_name: 'WhenPlayerChooseAbility', is_in_play_turn: false,
        prompt: { resetPromptText() {}, setTempPromptText() {} }, selectCountClear() {}, update() {} };
    const Music = { playClickCardSound() {} };
    const Replay = { prepared_replay: true };
    const FullSearchPresentation = { dismissIfActive: () => false, isActive: () => false };
    const Setting = { player_id: 0 };
    const ClientPreferences = { showDeckDuringFullSearch: () => false };
    const ButtonSetting = { auto_target: true, auto_target_forced: true, is_replay: false };
    const AutoEffect = { isAutoEffectTargeting: () => ButtonSetting.auto_target };
    const AutoActivate = { isHasAutoActivate: () => true, isAutoActivate: () => true,
        isAutoActivate2: () => true };
    const Cards = { getDiv: element, getSpanText: id => 'Weapon ' + id };
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
for (const name of ['data', 'select', 'btn_ok', 'effect', 'buttons']) {
    const source = fs.readFileSync(path.join(process.argv[2], name + '.js'), 'utf8')
        .replace(/^import .*\r?\n/gm, '')
        .replace(/^export /gm, '');
    vm.runInContext(source, context, { filename: name + '.js' });
}
vm.runInContext(`
    Effect.updateHighLight = () => {};
    Button.clean = () => {};
    Button.disablePause = () => {};
    for (const fixture of fixtures) {
        for (const autoTarget of [false, true]) {
            for (const choice of [0, 1]) {
                submissions.length = 0;
                Effect.reset();
                SelectStep.reset();
                ButtonSetting.auto_target = autoTarget;
                Effect.response_json_ask = new AskOptionPayload(fixture);
                Effect.setOptions();
                Effect.update();
                const options = Effect.response_json_ask.options;
                const buttons = Effect.options_button_div.childNodes;
                assert.equal(submissions.length, 0, 'Opening the flip decision must not submit it');
                assert.equal(JSON.stringify(buttons.map(button => button.innerHTML)),
                             JSON.stringify(options.map(option => option.name_with_space)));
                assert.equal(buttons.length, 2, 'Keep and Flip must both be visible');
                assert.equal(BtnOk.btn_ok_div.disabled, true, 'Neither outcome is chosen initially');
                const expected = options[choice];
                buttons[choice].click();
                assert.equal(submissions.length, 0, 'Selecting an optional outcome still requires confirmation');
                Button.doBtnOk();
                assert.equal(submissions.length, 1);
                assert.equal(submissions[0].id, expected.choice_id || expected.id);
                assert.equal(JSON.stringify(submissions[0].targets), JSON.stringify(expected.automatic_targets));
                assert.equal(submissions[0].resources.length, 0);
            }
        }
    }
`, context, { filename: 'psi-energy-choice-checks' });
