const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const createClient = require('./shuri_optional_discard_ui.cjs');
const fixture = process.argv[3] ? JSON.parse(fs.readFileSync(process.argv[3], 'utf8')) : null;
const context = createClient(process.argv[2], fixture);
vm.runInContext(`
    Effect.updateHighLight = () => {};
    Button.clean = () => {};
    Button.disablePause = () => {};
    Lib.string = { isNumeric: value => /^\\d+$/.test(value), isStringANumber: value => /^\\d+$/.test(value) };
    document.querySelectorAll = selector => selector === '.card'
        ? Array.from(Cards.records.keys(), element) : [];
    let postCalls = 0;
    const doPost = Button.doPost;
    Button.doPost = (...args) => { postCalls++; return doPost(...args); };

    function prepare(ask, cards, autoTarget = true, autoActivate = true) {
        submissions.length = 0;
        postCalls = 0;
        Effect.reset();
        SelectStep.reset();
        ButtonSetting.auto_target = autoTarget;
        ButtonSetting.auto_activate = autoActivate;
        ButtonSetting.is_replay = false;
        Setting.auto_effect_black_list = [];
        AutoActivate.config.clear();
        Cards.records = new Map(cards.map(card => [card.id, card]));
        for (const card of cards) {
            element(card.id).parentElement = element('table');
            element(card.id).classList.add(ClassName.auto_activate);
            AutoActivate.config.add(card.card_id);
        }
        UI.event_name = ask.event_name;
        Effect.response_json_ask = new AskOptionPayload(ask);
        Effect.setOptions();
    }
    function render() {
        Effect.update();
        Effect.update();
        assert.equal(submissions.length, 0, 'Rendering cannot send a gameplay command');
        assert.equal(postCalls, 0, 'Preselection cannot enter the submission path');
    }
    function confirm(option) {
        assert.equal(BtnOk.btn_ok_div.disabled, false, 'OK is ready for confirmation');
        Button.doBtnOk();
        assert.equal(submissions.length, 1);
        assert.equal(submissions[0].id, option.choice_id || option.id);
        Button.doBtnOk();
        assert.equal(submissions.length, 1, 'Repeated confirmation cannot submit twice');
    }
`, context);
if (fixture) {
    vm.runInContext(`
        const option = JSON.parse(fixtures.ask.options_json)[0];
        prepare(fixtures.ask, fixtures.cards);
        ClientPreferences.showDeckDuringFullSearch = () => !!fixtures.full_search;
        render();
        assert.equal(Effect.select_effect_obj.id, option.id);
        if (fixtures.expected_targets) {
            assert.deepEqual(Array.from(Effect.select_effect_obj.selected_targets), Array.from(fixtures.expected_targets),
                'All mandatory targets are preselected without clicking individual cards');
        }
        assert.equal(BtnOk.btn_ok_div.disabled, false);
        if (fixtures.accept) {
            if (Effect.isForcedTimingChoice()) {
                Button.doBtnCancel();
                assert.equal(submissions.length, 0, 'A forced response cannot be passed');
                render();
            }
            confirm(option);
        } else {
            Button.doBtnCancel();
            assert.equal(submissions.length, 1);
            assert.equal(submissions[0].id, undefined, 'Pass must not activate the response');
        }
    `, context);
    console.log(JSON.stringify(vm.runInContext('submissions[0]', context)));
} else {
    vm.runInContext(`
        const cards = [10, 11, 12, 13].map(id => ({ id, card_id: String(id),
            control_player: 0, effects: id === 10 ? [1, 2] : [], resources: id === 13 ? [9] : [] }));
        const base = { id: 1, choice_id: 'trigger-1', bind_id: 10, name: 'Named_Response',
            failure_reason: '', all_legal_targets: [11], target_num_range: [1, 1],
            automatic_targets: [11], automatic_submit: true, target_payment: {}, select_rule: '' };
        function ask(type, options = [base]) {
            return {ability_type: type, event_name: 'AfterPlayerPlayedCard',
                show_cancel: !type.startsWith('Forced'), options_json: JSON.stringify(options)};
        }
        for (const type of ['Response', 'ForcedResponse', 'Interrupt', 'ForcedInterrupt']) {
            for (const autoActivate of [false, true]) {
                for (const option of [base, {...base, all_legal_targets: [], target_num_range: [0, 0]},
                                      {...base, name: 'Ask'}]) {
                    prepare(ask(type, [option]), cards, true, autoActivate);
                    render();
                    assert.equal(Effect.select_effect_obj.id, option.id);
                    const targets = option.target_num_range[1] ? [11] : [];
                    assert.deepEqual(Array.from(Effect.select_effect_obj.selected_targets), targets);
                    if (type.startsWith('Forced')) {
                        Button.doBtnCancel();
                        assert.equal(submissions.length, 0, 'A forced prompt can deselect, but cannot pass');
                        render();
                    }
                    confirm(option);
                    assert.deepEqual(Array.from(submissions[0].targets), targets);
                }
            }
            // Selecting every required target still waits for an explicit OK.
            const all = {...base, all_legal_targets: [11, 12], target_num_range: [2, 2],
                         automatic_targets: [11, 12]};
            for (const fullSearch of [false, true]) {
                ClientPreferences.showDeckDuringFullSearch = () => fullSearch;
                prepare(ask(type, [all]), cards);
                render();
                assert.deepEqual(Array.from(Effect.select_effect_obj.selected_targets), [11, 12]);
                confirm(all);
                assert.deepEqual(Array.from(submissions[0].targets), [11, 12]);
            }
            // One card is not one choice: preserve distinct triggering conditions.
            for (const second of [{...base, id: 2, choice_id: 'trigger-2'}, {...base, choice_id: 'trigger-2'},
                                  {...base, id: 2, bind_id: 12, choice_id: 'trigger-2'}]) {
                prepare(ask(type, [base, second]), cards);
                render();
                assert.equal(Effect.select_effect_obj.id, -1);
                assert.equal(BtnOk.btn_ok_div.disabled, true);
                Effect.activeEffect(element(second.bind_id));
                if (second.bind_id === base.bind_id) {
                    Effect.options_button_div.childNodes[1].click();
                }
                render();
                confirm(second);
            }
            prepare(ask(type, [base, {...base, id: 2, failure_reason: 'Cannot pay'}]), cards);
            render();
            assert.equal(Effect.select_effect_obj.id, 1, 'Only eligible responses count');
            prepare(ask(type, [{...base, failure_reason: 'Cannot pay'}]), cards);
            render();
            assert.equal(Effect.select_effect_obj.id, -1);

            // Optional quantities, search results and force-choose targets stay manual.
            for (const change of [
                {target_num_range: [0, 1]}, {is_search: true},
                {full_search_display_targets: [11]}, {automatic_targets: []},
                {all_legal_targets: [11, 12], automatic_targets: []},
            ]) {
                prepare(ask(type, [{...base, ...change}]), cards);
                render();
                assert.equal(Effect.select_effect_obj.selected_targets.length, 0);
                if (change.target_num_range) {
                    confirm(base);
                    assert.equal(submissions[0].targets.length, 0, 'Confirming zero must stay zero');
                } else {
                    assert.equal(BtnOk.btn_ok_div.disabled, true);
                    Button.doBtnOk();
                    assert.equal(submissions.length, 0);
                }
            }
            for (const change of [
                {target_num_range: [1, 2]}, {automatic_targets: []},
                {automatic_targets: [11]}, {is_search: true},
                {full_search_display_targets: [11, 12]},
            ]) {
                prepare(ask(type, [{...all, ...change}]), cards);
                render();
                assert.equal(Effect.select_effect_obj.selected_targets.length, 0,
                    'Variable quantities and manual searches must remain a choice');
                assert.equal(BtnOk.btn_ok_div.disabled, true);
            }
            // Preselection respects Auto Target, blacklist and replay settings.
            for (const setting of ['manual', 'blacklist', 'replay']) {
                prepare(ask(type), cards, setting !== 'manual');
                if (setting === 'blacklist') Setting.auto_effect_black_list = ['10'];
                if (setting === 'replay') ButtonSetting.is_replay = true;
                render();
                assert.equal(Effect.select_effect_obj.id, -1);
                if (setting !== 'replay') {
                    Effect.activeEffect(element(10));
                    assert.equal(submissions.length, 0, 'Manual selection must also await OK');
                    confirm(base);
                }
            }
            // Refreshing must preserve a manually chosen target and payment.
            const paid = {...base, automatic_targets: [], all_legal_targets: [11, 12],
                target_payment: {12: {cost: 'R', rule: [], payment: [{effect_id: 9, res_text: 'R'}]}}};
            prepare(ask(type, [paid]), cards);
            render();
            Effect.onCardClick(element(12), false);
            assert.equal(submissions.length, 0);
            assert.equal(BtnOk.btn_ok_div.disabled, true, 'An unpaid cost cannot be confirmed');
            Effect.update();
            assert.deepEqual(Array.from(Effect.select_effect_obj.selected_targets), [12]);
            Effect.onCardClick(element(13), false);
            Effect.update();
            assert.deepEqual(Array.from(Effect.select_effect_obj.resources), [9]);
            assert.equal(submissions.length, 0);
            confirm(paid);
            assert.deepEqual(Array.from(submissions[0].resources), [9]);
        }
        prepare(ask('Response', [base, {...base, id: 3, name: 'Cancel', choice_id: 'cancel'}]), cards);
        render();
        assert.equal(Effect.select_effect_obj.id, 1);
        Button.doBtnCancel();
        assert.equal(submissions.length, 1);
        assert.equal(submissions[0].id, 'cancel');
    `, context);
    console.log(JSON.stringify({ok: true}));
}
