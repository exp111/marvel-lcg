const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Exercise compiled production methods with a deterministic DOM and network.
function makeDOM() {
    const elements = [];
    function createElement(tag) {
        const classes = new Set();
        const element = {
            tagName: tag, children: [], dataset: {}, style: {}, disabled: false,
            textContent: '', innerHTML: '',
            classList: {
                add: (...names) => names.forEach(name => classes.add(name)),
                remove: (...names) => names.forEach(name => classes.delete(name)),
                contains: name => classes.has(name),
            },
            setAttribute(name, value) { this[name] = value; },
            append(...children) {
                for (const child of children) {
                    child.parent = this;
                    this.children.push(child);
                }
            },
            appendChild(child) { this.append(child); },
            remove() {
                if (this.parent) this.parent.children = this.parent.children.filter(x => x !== this);
                this.removed = true;
            },
            focus() { document.activeElement = this; },
            addEventListener(name, listener) { this['on' + name] = listener; },
        };
        elements.push(element);
        return element;
    }
    const document = {
        createElement, location: { pathname: '/replay' },
        getElementById(id) {
            return elements.find(x => x.id === id && !x.removed) || null;
        },
        querySelector(selector) { return this.getElementById(selector.slice(1)); },
        querySelectorAll() { return []; },
    };
    document.body = createElement('body');
    for (const id of ['goto-id', 'replay-btn', 'message-overlay', 'message-text',
        'game-over-box', 'game-over-text', 'game-over-text-2', 'game-over-buttons',
        'replay-items', 'puzzle-items']) {
        const element = createElement('div');
        element.id = id;
        document.body.append(element);
    }
    return document;
}

function jsonResponse(result, status = 200) {
    return {
        ok: status === 200, status,
        headers: { get: () => 'application/json' },
        json: async () => result,
    };
}

async function testClient() {
    const document = makeDOM();
    const responses = [], requests = [], notices = [], timers = [], debug = [];
    let syncs = 0;
    const window = {
        location: { href: 'http://localhost/?hot_seat&3d_scene&replay' },
        history: { replaceState(_state, _title, url) { window.location.href = String(url); } },
    };
    const context = vm.createContext({
        document, window, URL, Error, console,
        setTimeout(callback) { timers.push(callback); },
        fetch: async (url, options) => {
            requests.push({ url, options });
            assert.ok(responses.length, 'Unexpected request: ' + url);
            return await responses.shift();
        },
        Notify: { create: (...args) => notices.push(args) },
        Game: { is_lost_connect: false, players_won: true },
        ButtonSetting: { is_replay: 1 }, Setting: { player_id: 0 },
        Client: { doSyncGame() { syncs++; } },
        Effect: { response_json_ask: { replay_finished: false, replay_input: '{"id":":debug"}' } },
        SelectStep: { isCost: () => false }, Cards: {},
        BtnOk: { setDisable(value) { this.disabled = value; } },
        FullSearchPresentation: { isActive: () => false },
    });
    for (const name of ['command', 'buttons', 'replay', 'message']) {
        const source = fs.readFileSync(path.join(process.argv[2], name + '.js'), 'utf8')
            .replace(/^import .*\r?\n/gm, '').replace(/^export /gm, '');
        vm.runInContext(source, context, { filename: name + '.js' });
    }
    const { Command, Button, Replay, Message } = vm.runInContext('({Command, Button, Replay, Message})', context);
    Button.doDebug = command => debug.push(command);

    responses.push(jsonResponse({ path: 'C:/replays/full-game.json' }));
    await Command.saveLocal();
    assert.equal(requests[0].url, 'save_local');
    assert.equal(requests[0].options.method, 'POST');
    assert.equal(notices.at(-1)[0], 'REPLAY');
    assert.match(notices.at(-1)[2], /C:\/replays\/full-game.json.*main menu/);

    responses.push(jsonResponse({ error: 'Folder is not writable' }, 500));
    await Command.saveLocal();
    assert.equal(notices.at(-1)[0], 'SAVE FAILED');
    assert.match(notices.at(-1)[2], /Folder is not writable/);
    responses.push({ ok: true, headers: { get: () => 'image/jpeg' }, json() { throw Error('binary must not be parsed'); } });
    await Command.saveLocal();
    assert.equal(notices.at(-1)[0], 'SAVE FAILED');
    assert.match(notices.at(-1)[2], /unexpected save response/);

    let finishSave;
    responses.push(new Promise(resolve => { finishSave = resolve; }));
    const requestCount = requests.length;
    const pending = Command.saveLocal();
    await Command.saveLocal();
    assert.equal(requests.length, requestCount + 1, 'Double clicks must not create duplicate saves');
    finishSave(jsonResponse({ path: 'C:/replays/another-game.json' }));
    await pending;

    Replay.setWatching(true);
    Replay.doReplay();
    await timers.shift()(); // A submission is now scheduled.
    context.Effect.response_json_ask = { replay_finished: true, replay_input: '{}' };
    Replay.onPrompt();
    Replay.onPrompt();
    const dialog = document.getElementById('replay-end-dialog');
    assert.ok(dialog);
    assert.equal(document.body.children.filter(x => x.id === 'replay-end-dialog').length, 1);
    const [title, description, continueButton, libraryButton] = dialog.children[0].children;
    assert.equal(title.textContent, 'End of recording');
    assert.equal(document.activeElement, continueButton);
    assert.equal(context.BtnOk.disabled, true);
    Button.doPost(); Button.doCancel(); Button.doNext();
    assert.equal(debug.length, 0);

    responses.push(jsonResponse({ error: 'The recording has not ended' }, 409));
    await continueButton.onclick();
    assert.equal(Replay.finished, true);
    assert.equal(continueButton.disabled, false);
    assert.match(description.textContent, /recording has not ended/);
    assert.equal(syncs, 0);

    document.body.classList.add('replaying');
    document.getElementById('replay-btn').classList.add('clicked');
    responses.push(jsonResponse({ result: 'Continue playing' }));
    await continueButton.onclick();
    assert.equal(requests.at(-1).url, 'continue_replay');
    assert.equal(requests.at(-1).options.method, 'POST');
    assert.equal(Replay.finished, false);
    assert.equal(Replay.is_watching, false);
    assert.equal(context.ButtonSetting.is_replay, 0);
    assert.equal(document.getElementById('replay-end-dialog'), null);
    assert.equal(document.body.classList.contains('replaying'), false);
    assert.equal(new URL(window.location.href).searchParams.has('replay'), false);
    assert.equal(syncs, 1);
    await timers.shift()();
    assert.equal(debug.length, 0, 'An old replay timer must not submit a choice after Continue');
    Button.doNext();
    assert.equal(debug.length, 1, 'Normal controls become available after Continue succeeds');

    Replay.setWatching(true);
    Message.init();
    Message.showGameOverMessage('The Final Stage of the Villain was Defeated');
    assert.match(document.getElementById('game-over-text').textContent, /Replay complete.*VICTORY/);
    context.Game.players_won = false;
    Message.showGameOverMessage('All players were eliminated');
    assert.match(document.getElementById('game-over-text').textContent, /Replay complete.*DEFEAT/);
    Replay.setWatching(false);
    Message.showGameOverMessage('All players were eliminated');
    assert.equal(document.getElementById('game-over-text').textContent, 'DEFEAT');
    libraryButton.onclick();
    assert.equal(window.location.href, '/replay');
}

async function testLibrary() {
    const document = makeDOM(), requests = [], opened = [];
    let complete = false, status = 200;
    const context = vm.createContext({
        document, console,
        window: { open: url => opened.push(url) },
        fetch: async url => jsonResponse(url.startsWith('list_') ? [] : {
            players: ['Spider-Man'], villain: 'Rhino', step: 10, seed: 122,
            replay_complete: complete,
        }),
        XMLHttpRequest: class {
            open(method, url) { requests.push({ method, url }); }
            send() { this.readyState = 4; this.status = status; this.onreadystatechange(); }
        },
    });
    const html = fs.readFileSync(path.join(__dirname, '../public/replay.html'), 'utf8');
    for (const script of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) vm.runInContext(script[1], context);
    const createItem = vm.runInContext('create_item', context);
    const item = await createItem('C:/replays/game.json', true);
    const [watch, resume] = item.children[2].children;
    assert.equal(watch.textContent, 'Watch replay');
    assert.equal(resume.textContent, 'Resume game');
    assert.equal(resume.disabled, false);
    watch.onclick({ stopPropagation() {} });
    assert.equal(requests.at(-1).url, 'load_replay?C:/replays/game.json');
    assert.match(opened.at(-1), /&replay$/);
    resume.onclick({ stopPropagation() {} });
    assert.equal(requests.at(-1).url, 'resume_replay?C:/replays/game.json');
    assert.ok(!opened.at(-1).includes('replay'));
    complete = true;
    const finishedItem = await createItem('C:/replays/finished.json', true);
    assert.equal(finishedItem.children[2].children[1].disabled, true);
    status = 500;
    const openedCount = opened.length;
    watch.onclick({ stopPropagation() {} });
    assert.equal(opened.length, openedCount, 'Failed loads must not open a gameplay tab');
}

(async () => {
    await testClient();
    await testLibrary();
    console.log('Replay library UI regressions passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
