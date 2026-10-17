const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'public/deck.html'), 'utf8');
const script = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)]
    .map(match => match[1]).find(source => source.includes('async function getHeroJson('));

class Element {
    constructor() {
        this.children = [];
        this.attributes = {};
        this.value = '';
        this.classList = {add() {}};
    }
    appendChild(child) { this.children.push(child); }
    replaceChildren() { this.children = []; }
    setAttribute(key, value) { this.attributes[key] = value; }
}

const elements = new Map();
const document = {
    createElement: () => new Element(),
    querySelector(selector) {
        if (!elements.has(selector)) elements.set(selector, new Element());
        return elements.get(selector);
    },
};
let clipboard = '';
let opened = '';
const context = vm.createContext({
    document,
    window: {
        cardImages: {setImage(image, id) { image.src = id; }},
        open(url) { opened = url; },
    },
    prompt: () => clipboard,
    btoa: text => Buffer.from(text).toString('base64'),
    alert: message => assert.fail(message),
});
vm.runInContext(script, context);

function readDeck(name) {
    return JSON.parse(fs.readFileSync(path.join(root, 'deck/starter', name + '.json'), 'utf8'));
}

function assertRendered(deck) {
    const expected = {
        hero_images: deck.hero.flatMap(id => id.split(',')),
        hero_obligation: [...deck.obligations, ...deck.nemesis_set].flatMap(id => id.split(',')),
        hero_set_aside: (deck.set_aside || []).flatMap(id => id.split(',')),
        side_deck_images: (deck.side_deck || []).flatMap(id => id.split(',')),
        hero_deck_images: deck.hero_deck,
        player_deck_images: deck.player_deck,
    };
    for (const [id, cards] of Object.entries(expected)) {
        const rendered = document.querySelector('#' + id).children
            .map(element => element.attributes['data-card-id']);
        assert.deepEqual(rendered, cards, `${deck.name}: ${id}`);
    }
    assert.equal(document.querySelector('#hero_deck').value, deck.hero_deck.join('; '));
    assert.equal(document.querySelector('#slots').value, deck.player_deck.join('; '));
    assert.equal(document.querySelector('#set_aside').value, (deck.set_aside || []).join('; '));
    assert.equal(document.querySelector('#side_deck').value, (deck.side_deck || []).join('; '));
    assert.equal(document.querySelector('#player_deck_images_size').innerHTML, `size: ${deck.player_deck.length}`);
    assert.equal(document.querySelector('#side_deck_images_size').innerHTML, `size: ${(deck.side_deck || []).length}`);
}

function select(deck) {
    context.hero_data = structuredClone(deck);
    context.showDeckCards();
    assertRendered(deck);
}

(async () => {
    // Reproduce the reported switch, including clearing Iceman's extra cards
    // and a previously edited side deck when the next deck omits both lists.
    const iceman = readDeck('iceman');
    iceman.side_deck = ['01088'];
    for (const deck of [iceman, readDeck('jessica_jones'), readDeck('luke_cage'), iceman]) {
        select(deck);
        context.updatePlayerDeck();
        assertRendered(deck);
        context.play();
        const payload = JSON.parse(Buffer.from(opened.split('?deck=')[1], 'base64').toString());
        assert.equal(payload.name, deck.name);
        assert.deepEqual(payload.hero, deck.hero);
        assert.deepEqual(payload.hero_deck, deck.hero_deck);
        assert.deepEqual(payload.player_deck, deck.player_deck);
        assert.deepEqual(payload.set_aside, deck.set_aside || []);
        assert.deepEqual(payload.side_deck, deck.side_deck || []);
    }

    const files = fs.readdirSync(path.join(root, 'deck/starter')).filter(file => file.endsWith('.json'));
    for (const file of files) select(readDeck(file.slice(0, -5)));

    // Old exported decks and local/clipboard imports use the same renderer.
    const imported = readDeck('jessica_jones');
    imported.set_aside = null;
    imported.side_deck = null;
    await context.loadDeck({files: [{text: async () => JSON.stringify(imported)}]});
    assertRendered(imported);
    clipboard = JSON.stringify(readDeck('luke_cage'));
    await context.importDeck();
    assertRendered(JSON.parse(clipboard));
    console.log(`Deck editor: ${files.length} starters, hero switching, edits, Play payloads and imports passed.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
