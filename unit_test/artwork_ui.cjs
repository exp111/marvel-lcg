const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const nodes = new Map();
function element() {
    return { textContent: '', hidden: false, disabled: false, style: {}, children: [],
        setAttribute() {}, appendChild(child) { this.children.push(child); },
        remove() { this.removed = true; } };
}
for (const id of ['state', 'message', 'progress', 'cards', 'packs', 'download', 'installed', 'required', 'folder', 'errors', 'pause', 'resume', 'retry', 'continue']) nodes.set(id, element());
const state = {
    state: 'downloading', ready: false, can_play: false, completed_cards: 2, total_cards: 5,
    completed_packs: 1, total_packs: 2, downloaded_bytes: 128, total_bytes: 1024,
    installed_bytes: 512, required_bytes: 2048, folder: 'Artwork', errors: {},
    required_storage_bytes: 4096, total_installed_bytes: 3072,
};
const requests = [], timers = [], destinations = [], body = element();
const context = vm.createContext({
    URL, URLSearchParams,
    document: { getElementById: id => nodes.get(id), createElement: element, body },
    location: { origin: 'http://localhost', search: '', replace: path => destinations.push(path), assign: path => destinations.push(path) },
    window: { setTimeout: callback => { timers.push(callback); return timers.length; }, clearTimeout() {}, addEventListener() {} },
    async fetch(url, options) {
        requests.push({url, options});
        if (url === '/artwork_action') state.state = JSON.parse(options.body).action === 'pause' ? 'paused' : 'downloading';
        return {ok: true, headers: {get: () => 'application/json'}, json: async () => ({...state})};
    },
});
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8').replace(/^export /gm, '') + '\nglobalThis.artwork = {startArtworkPage, artworkDestination, formatArtworkBytes, showArtworkPreparation};', context);
const artwork = context.artwork;
async function flush() { for (let i = 0; i < 12; i++) await Promise.resolve(); }
(async () => {
    assert.equal(artwork.artworkDestination('/deck?v=1', 'http://localhost'), '/deck?v=1');
    for (const raw of ['https://evil.invalid/deck', '//evil.invalid/deck', '/new?data=anything', '/load_replay?save.json', 'http://[invalid']) {
        assert.equal(artwork.artworkDestination(raw, 'http://localhost'), '/main');
    }
    assert(artwork.formatArtworkBytes(1024).includes('1,024 bytes'));
    artwork.startArtworkPage();
    await flush();
    assert.equal(nodes.get('cards').textContent, '2 / 5');
    assert(nodes.get('download').textContent.includes('128 bytes'));
    assert(nodes.get('required').textContent.includes('4,096 bytes'));
    assert.equal(nodes.get('pause').disabled, false);
    assert.equal(nodes.get('continue').disabled, true);
    nodes.get('pause').onclick();
    await flush();
    assert.equal(nodes.get('resume').disabled, false);
    assert.equal(requests.at(-1).options.body, '{"action":"pause"}');
    state.state = 'incomplete'; state.error = 'Missing approved cards';
    await timers.shift()();
    assert.equal(nodes.get('continue').disabled, true);
    assert.equal(nodes.get('retry').disabled, true);
    assert.equal(nodes.get('errors').textContent, 'Missing approved cards');
    state.state = 'ready'; state.ready = state.can_play = true; state.error = '';
    await timers.shift()();
    assert.equal(nodes.get('continue').disabled, false);
    nodes.get('continue').onclick();
    assert.deepEqual(destinations, ['/main']);
    let retries = 0;
    artwork.showArtworkPreparation(() => retries++);
    const notice = body.children.at(-1);
    assert.equal(notice.children[1].href, '/artwork');
    assert.equal(notice.children[1].target, '_blank');
    notice.children[2].onclick();
    assert.equal(retries, 1, 'Retry retains the original selection/upload closure');
    console.log('Artwork preparation UI regression passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
