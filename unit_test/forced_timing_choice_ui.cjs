const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Run the compiled client with minimal DOM/audio stubs. Selection, prompt
// classification, button state and cancel routing are the production methods.
const elements = new Map();
function element(id) {
    if (!elements.has(id)) {
        const classes = new Set();
        elements.set(id, {
            disabled: false, innerHTML: '', dataset: {},
            classList: {
                add: (...names) => names.forEach(name => classes.add(name)),
                remove: (...names) => names.forEach(name => classes.delete(name)),
                contains: name => classes.has(name),
            },
            replaceChildren() {},
        });
    }
    return elements.get(id);
}
const context = vm.createContext({
    assert, structuredClone, window: {}, console: { log() {} },
    document: {
        getElementById: element,
        querySelector: () => null,
        querySelectorAll: () => [],
    },
});
vm.runInContext(`
    const Lib = { array: { occurrence: (items, item) => items.filter(x => x === item).length } };
    const Game = { is_lost_connect: false };
    const UI = { event_name: '', prompt: { resetPromptText() {} }, selectCountClear() {}, update() {} };
    const Music = { playClickCardSound() {} };
    const Replay = { prepared_replay: true };
    const FullSearchPresentation = { dismissIfActive: () => false, isActive: () => false };
    const Setting = { player_id: 0 };
    const ClientPreferences = { showDeckDuringFullSearch: () => false };
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

    function prompt(abilityType, eventName, showCancel, options) {
        Effect.select_effect_obj.clear();
        SelectStep.reset();
        Effect.response_json_ask = new AskOptionPayload({
            options_json: JSON.stringify(options), ability_type: abilityType,
            event_name: eventName, show_cancel: showCancel,
        });
        Effect.setOptions();
    }
    const temporaries = [44, 45].map((cardId, index) => ({
        id: 231 + index, choice_id: 'timing-0-' + (231 + index) + '-2394',
        bind_id: cardId, name: 'The_Best_Offense...:_Temporary',
        target_num_range: [0, 0], failure_reason: '',
    }));

    for (const abilityType of ['ForcedInterrupt', 'ForcedResponse']) {
        prompt(abilityType, 'WhenRoundEnd', false, temporaries);
        assert.equal(Effect.is_in_event, abilityType === 'ForcedInterrupt' ? 'interrupt' : 'response');
        assert.equal(BtnOk.btn_end_div.disabled, true);
        assert.equal(BtnOk.btn_end_div.classList.contains('forced_action'), true);
        Button.doBtnCancel();
        Button.doCancel(); // Also guard direct callers, regardless of DOM state.
        assert.equal(submissions.length, 0);
        assert.equal(Effect.response_json_ask.options.length, 2);

        Effect.select_effect_obj = new EffectDescriptor(Effect.response_json_ask.options[0]);
        SelectStep.restoreStep('target');
        BtnOk.setDisable(false);
        BtnOk.setCancel('Cancel');
        assert.equal(BtnOk.btn_end_div.disabled, false);
        assert.equal(BtnOk.btn_end_div.innerHTML, 'Cancel');
        Button.doBtnCancel();
        assert.equal(submissions.length, 0);
        assert.equal(SelectStep.isCard(), true);
        assert.equal(BtnOk.btn_end_div.disabled, true);
        assert.equal(Effect.response_json_ask.options.length, 2);

        // Selecting and confirming either Temporary still reaches the submit route.
        for (const option of Effect.response_json_ask.options) {
            Effect.select_effect_obj = new EffectDescriptor(option);
            SelectStep.restoreStep('cost');
            BtnOk.setOk('OK');
            const before = submissions.length;
            Button.doBtnOk();
            assert.equal(submissions.length, before + 1);
            assert.equal(submissions[before].id, option.choice_id);
        }
        submissions.length = 0;
    }

    for (const abilityType of ['Interrupt', 'Response']) {
        prompt(abilityType, 'WhenRoundEnd', true, temporaries);
        assert.equal(BtnOk.btn_end_div.disabled, false);
        const before = submissions.length;
        Button.doBtnCancel();
        assert.equal(submissions.length, before + 1);
        assert.equal(submissions[before].id, undefined);
    }

    // An explicit optional Cancel inside a forced effect remains selectable.
    prompt('Normal', 'WhenPlayerChooseAbility', false, [
        temporaries[0], { id: 999, name: 'Cancel', target_num_range: [0, 0] },
    ]);
    assert.equal(BtnOk.btn_end_div.disabled, false);
    const before = submissions.length;
    Button.doBtnCancel();
    assert.equal(submissions.length, before + 1);
    assert.equal(submissions[before].id, 999);

    // The existing forced end-turn hand discard cannot be canceled either.
    prompt('Normal', 'End Turn', false, [{
        id: 7, name: 'End_Phase', target_num_range: [1, 6], failure_reason: '',
    }]);
    Effect.select_effect_obj = Effect.response_json_ask.options[0];
    SelectStep.restoreStep('target');
    const beforeDiscardCancel = submissions.length;
    Button.doBtnCancel();
    Button.doCancel();
    assert.equal(submissions.length, beforeDiscardCancel);
`, context, { filename: 'forced-choice-checks' });
