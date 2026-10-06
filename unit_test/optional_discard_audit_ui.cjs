const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const createClient = require('./shuri_optional_discard_ui.cjs');
const context = createClient(process.argv[2], JSON.parse(fs.readFileSync(process.argv[3], 'utf8')));
vm.runInContext(`
    Effect.updateHighLight = () => {};
    Button.clean = () => {};
    Button.disablePause = () => {};
    for (const fixture of fixtures) {
        for (const autoTarget of [false, true]) {
            for (const autoActivate of [false, true]) {
                for (const accept of [false, true]) {
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
                    Effect.update();
                    const option = Effect.response_json_ask.options[0];
                    const optionId = option.choice_id || option.id;
                    assert.equal(submissions.length, 0, 'Opening an optional discard must not submit it');
                    if (fixture.optional_count) {
                        assert.equal(Effect.select_effect_obj.selected_targets.length, 0,
                                     'An optional discard count must start at zero');
                    }
                    if (accept) {
                        const desired = option.all_legal_targets.slice(0, option.target_num_range[1]);
                        for (const target of desired) {
                            if (!Effect.select_effect_obj.selected_targets.includes(target)) {
                                Effect.onCardClick(element(target), false);
                            }
                        }
                        Button.doBtnOk();
                        assert.equal(submissions.length, 1);
                        assert.equal(submissions[0].id, optionId);
                        assert.equal(submissions[0].targets.length, desired.length);
                    } else {
                        Button.doBtnCancel();
                        assert.equal(submissions.length, 1);
                        assert.equal(submissions[0].id, undefined);
                    }
                }
            }
        }
    }
`, context, { filename: 'optional-discard-audit-checks' });
