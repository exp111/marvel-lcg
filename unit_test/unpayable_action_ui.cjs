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
    Lib.string = { isNumeric: value => /^-?\\d+$/.test(value),
                   isStringANumber: value => /^\\d+$/.test(value) };
    document.querySelectorAll = selector => selector === '.card'
        ? Array.from(Cards.records.keys(), element) : [];
    function prepare(ask, cards, autoTarget = true, autoActivate = true) {
        submissions.length = 0;
        Effect.reset();
        SelectStep.reset();
        ButtonSetting.auto_target = autoTarget;
        ButtonSetting.auto_activate = autoActivate;
        ButtonSetting.is_replay = false;
        AutoActivate.config.clear();
        Cards.records = new Map(cards.map(card => [card.id, card]));
        for (const card of cards) {
            element(card.id).parentElement = element('table');
            element(card.id).dataset.pay_effect_id = '';
            element(card.id).classList.add(ClassName.auto_activate);
            AutoActivate.config.add(card.card_id);
        }
        UI.event_name = ask.event_name;
        UI.is_in_play_turn = ask.event_name === 'WhenPlayerInTurn';
        Effect.response_json_ask = new AskOptionPayload(ask);
        Effect.setOptions();
    }
`, context);
if (fixture) {
    vm.runInContext(`
        for (const autoTarget of [false, true]) {
            for (const autoActivate of [false, true]) {
                prepare(fixtures.ask, fixtures.cards, autoTarget, autoActivate);
                Effect.update();
                assert.equal(Effect.isCardHasEffect(fixtures.blocked_card), false,
                    'Stick-To-Itiveness must not glow without a physical or wild resource');
                Effect.onCardClick(element(fixtures.blocked_card), false);
                Effect.update();
                Button.doBtnOk();
                assert.equal(submissions.length, 0, 'Clicking the unpayable upgrade cannot submit');
            }
        }
    `, context);
} else {
    vm.runInContext(`
        const cards = [
            {id: 10, card_id: '44030', control_player: 0, effects: [1], resources: []},
            {id: 11, card_id: '45001a', control_player: 0, effects: [], resources: []},
            {id: 12, card_id: '01090', control_player: 0, effects: [], resources: [90]},
        ];
        const base = {id: 1, name: 'Hero_Action', bind_id: 10, bind_player_id: 0,
            failure_reason: '', all_legal_targets: [11], target_num_range: [1, 1],
            automatic_targets: [11], automatic_submit: true, select_rule: '',
            target_payment: {0: {cost: 'R', rule: [], payment: []}}};
        function ask(option) {
            return {options_json: JSON.stringify([option]), ability_type: 'Normal',
                    event_name: 'WhenPlayerInTurn', show_cancel: true};
        }
        // Also exercise the final submission guard with an older/stale
        // descriptor, bypassing the normal card-availability UI entirely.
        for (const payment of [
            {cost: 'R', rule: [], payment: []},
            {cost: '2', rule: [], payment: [{90: 'R'}]},
            {cost: 'R', rule: [], payment: [{90: 'Y'}]},
        ]) {
            const option = {...base, target_payment: {0: payment}};
            prepare(ask(option), cards);
            Effect.select_effect_obj = new EffectDescriptor(option);
            SelectStep.setTargets();
            Button.doPost(true);
            assert.equal(submissions.length, 0, 'An empty payment is not a free action');
            Effect.select_effect_obj.resources = payment.payment.length ? [90] : [];
            Button.doPost(false);
            assert.equal(submissions.length, 0, 'Insufficient or wrong resources cannot be submitted');
            assert.equal(BtnOk.btn_ok_div.disabled, true);
            Button.doBtnCancel();
            assert.equal(submissions.length, 0, 'Cancel payment returns to the player turn');
        }
        // Required costs without any payment sources are not activatable;
        // free alternatives, up-to payments, and payable targets stay legal.
        for (const [payments, available] of [
            [{0: {cost: 'R', rule: [], payment: []}}, false],
            [{0: {cost: '2', rule: [], payment: []}}, false],
            [{0: {cost: 'B|2', rule: [], payment: []}}, false],
            [{0: {cost: '0', rule: [], payment: []}}, true],
            [{0: {cost: 'R|0', rule: [], payment: []}}, true],
            [{0: {cost: 'R', rule: ['UpTo'], payment: []}}, true],
            [{0: {cost: 'R', rule: [], payment: [{90: 'G'}]}}, true],
            [{11: {cost: 'R', rule: [], payment: []},
              12: {cost: '0', rule: [], payment: []}}, true],
            [{}, true],
        ]) {
            const option = {...base, target_payment: payments};
            prepare(ask(option), cards);
            assert.equal(Effect.isCardHasEffect(10), available);
        }
        // Both printed physical and wild resources pay the real typed cost.
        for (const resource of ['R', 'G', 'RR']) {
            const option = {...base, target_payment: {0: {cost: 'R', rule: [], payment: [{90: resource}]}}};
            prepare(ask(option), cards);
            Effect.activeEffect(element(10));
            assert.equal(submissions.length, 0, 'Selecting an action must await its payment');
            Effect.onCardClick(element(12), false);
            Button.doBtnOk();
            assert.equal(submissions.length, 1);
            assert.deepEqual(Array.from(submissions[0].resources), [90]);
        }
        for (const payment of [
            {cost: '0', rule: [], payment: []},
            {cost: 'R|0', rule: [], payment: []},
            {cost: 'R', rule: ['UpTo'], payment: []},
        ]) {
            const option = {...base, target_payment: {0: payment}};
            prepare(ask(option), cards);
            Effect.activeEffect(element(10));
            assert.equal(submissions.length, 1, 'A legal zero-resource action still resolves');
            assert.deepEqual(Array.from(submissions[0].resources), []);
        }
    `, context);
}
console.log(JSON.stringify({ok: true}));
