# Release 1.0 patch set

Application version: **0.5.9.202r**

Baseline: Irefrixs Team upstream `master` at `a77154a`

These notes describe the final behavior in this community release. Superseded experiments and reverted implementations are intentionally omitted.

## Highlights

- Added complete digital campaign flows for **Mutant Genesis**, **NeXt Evolution**, **Age of Apocalypse**, **Agents of S.H.I.E.L.D.**, **Galaxy's Most Wanted**, and **The Mad Titan's Shadow**.
- Added the **Wonder Man** and **Hercules** hero expansions, including starter decks, hero cards, obligations, and nemesis content.
- Added the **Synthezoid Smackdown** cooperative content, including She-Hulk and Vision scenarios and eight modular encounter sets.
- Added an adjustable card-interaction speed setting that changes presentation timing without changing game-state resolution.
- Corrected campaign-card transitions, distributed threat and damage selection, attachment behavior, resource reductions, and numerous individual card scripts.

## Campaign support

- Added a campaign selector with stable internal campaign identifiers so campaign setup, logs, replay data, and saved state select the intended campaign reliably.
- Retained selection support for **The Rise of Red Skull** and **Sinister Motives** alongside the six newly implemented campaign flows.
- Added campaign-log card previews with a fixed, readable tooltip size and position.
- Added campaign-specific setup screens, scenario progression, persistent rewards and penalties, campaign pools, and scenario-dependent setup instructions.
- Added Mutant Genesis role and reward content for **Brawler**, **Commander**, **Defender**, and **Peacekeeper**, plus the campaign player side schemes and Magneto campaign cards.
- Added the NeXt Evolution campaign player side schemes and their scenario-specific setup and persistence rules.
- Added Age of Apocalypse campaign missions, mission allies, overseers, mission attempts, campaign setup choices, and campaign upgrades.
- Added Agents of S.H.I.E.L.D. campaign progression, evidence and Executive Board state, and scenario setup choices.
- Added Galaxy's Most Wanted credits, market purchases, ship upgrades, and scenario progression.
- Added The Mad Titan's Shadow campaign cards, scenario progression, and campaign state used across its five scenarios.

## Added content packs

### Synthezoid Smackdown

- Added standard and expert scenario definitions for **She-Hulk** and **Vision**.
- Added the **Deadly Duo**, **Moon Knight**, **Royal Guard**, **Scarlet Twins**, **S.H.I.E.L.D. Ops**, **Taskmaster**, **Thunderbolts**, and **Young Avengers** modular encounter sets.
- Added encounter scripting for the She-Hulk and Vision scenario sets, including form interactions, attachments, boost effects, defeated-side-scheme effects, and encounter-card targeting.
- Added the set image and all required database and encounter-set registrations.

### Wonder Man

- Added Wonder Man's identity, hero kit, obligation, and nemesis set.
- Added the Wonder Man starter deck and supporting player cards included with the pack.
- Added mechanics for ionic counters, discard-based costs, identity-specific targeting, and Wonder Man's campaign/player-card interactions.
- Added the set image and card-database registration.

### Hercules

- Added Hercules's identity, hero kit, obligation-related content, and supporting player cards.
- Added the Hercules starter deck.
- Added mechanics for glory counters, side-scheme interaction, printed threat restoration, and Hercules-specific costs and responses.
- Added the set image and card-database registration.

## Gameplay and card corrections

### Campaign cards

- **Magneto's Fortress / Magneto's Power:** flipping the side scheme now puts Magneto's Power into play attached to Magneto, so its SCH and ATK modifiers apply.
- **Orbital Decay / Physical Strain:** Physical Strain now enters play attached to Magneto after the side scheme flips, allowing its Steady reduction to function.
- Corrected flipped campaign permanents and player side schemes so their reverse faces enter the correct play area instead of remaining detached after a raw card flip.
- Corrected Age of Apocalypse overseer name matching, multi-resource mission matches, player choice when more than one resource matches, Professor X checks, and mission reward values.
- Corrected Agents of S.H.I.E.L.D. Board Member cards so they attach to the villain and the third attachment ends the game as required.
- Corrected Galaxy's Most Wanted market purchases to discard purchased cards rather than remove them from the game, corrected **Close Call** to a Hero Interrupt, and prevented forced random-discard effects from prompting against an empty hand.
- Corrected Sinister Motives S.H.I.E.L.D. Tech ownership and stat application, basic-thwart restrictions, the correct side of **Shock Knuckles** receiving its ATK bonus, and empty-hand handling for **Back Alley Burglary**.
- Corrected **Improved Recovery Upgrade** so using its recovery bonus exhausts the upgrade.
- Corrected campaign metadata, setup flags, unit costs, incite values, victory values, card wording, and the card-database checksum.

### Threat and damage distribution

- Added an exact-up-to-available target range for effects that distribute a fixed total. Players must now allocate the full legal amount while still being allowed to resolve an effect when fewer valid threat or health points exist.
- **Surprise!** now removes up to 3 total threat, distributed among schemes as chosen, and then confuses the villain.
- Corrected distributed selection for **Heroic Intervention**, **Mentorship**, **Gunboat Diplomacy**, **Mutant Peacekeepers**, **Torrential Rain**, **Inconspicuous**, and **Giant Help**.
- Corrected **Mutant Peacekeepers** so its final threat value is calculated after choosing and exhausting participating X-Men allies.
- **Shadowcat** can now select a side scheme with zero threat when placing threat through her response.

### Added-pack audit corrections

- **Embody Pathos** now restores a side scheme's one-player starting threat plus its one-player hinder value before attaching.
- **Ancient Rivalry** now performs its required identity-specific search rather than presenting it as optional.
- Corrected **Jester's Yo-Yo** and **Mimicked Move** boost effects.
- Corrected **Deadly Duo**, **Superpowered Siblings**, and **Just Passing Through** to resolve their defeated-side-scheme effects at the proper timing and against the defeating player.
- Corrected **Superspeed** so its reveal and boost branches use the appropriate random or chosen discard behavior.
- Corrected **Gamma Slam** to gain surge when its threat cannot be placed.
- Corrected **Legal Practice** to respond after changing to alter-ego form and exhaust the identity as its cost.
- Corrected Taskmaster's reveal activation, Sword and Shield resource costs, and the Thunderbolts trait check.
- Implemented the missing **Solar Gem** and **Vision's Cape** attachment, response, form-flip, and boost behavior.
- Corrected **Superdense Strike** and **Phase Disruption** to inspect and flip the correct Vision mass-form attachment and to affect the correct target.
- Corrected **Disarming Defense** to use Hero Interrupt timing.
- Corrected **Pacifism** so its attack restriction applies to the attached identity.

### Attack and condition interactions

- Corrected attached-identity defense restrictions so they bind to the attached player instead of being interpreted as a card finder. This prevents attack windows from suppressing or breaking otherwise legal identity abilities, including Nightcrawler interactions.
- Confirmed through regression coverage that shared play-cost reducers subtract from the actual play cost and that **Uncanny X-Men** applies only to its controller.

## Interface, hotseat, and loading improvements

- Improved MarvelCDB deck imports by selecting heroes from the returned hero name and preserving non-hero cards in campaign decks that intentionally violate normal deckbuilding validation.
- Updated Enter and Escape hotkeys to respect the active prompt, disabled buttons, card-selection steps, and cancellation state.
- Prevented duplicate submissions while a choice or cost request is already being posted.
- Improved hotseat prompt ownership so the interface focuses the player bound to the returned choice instead of relying on stale waiting-player state.
- Corrected right-click and hover behavior when hotseat rendering replaces a card without generating a new mouse-enter event.
- Corrected transformed-board pointer hit testing so visible cards receive clicks even when an empty 3D camera plane overlaps them.
- Added reliable no-cache headers, a complete browser cache-clear response, and version parameters for static and dynamic JavaScript imports.
- Added MarvelCDB as a fallback card-image server, stopped empty placeholder responses from being cached as downloaded art, and improved generated missing-image placeholders.
- Increased the application build number to **0.5.9.202**.

## Card interaction speed setting

- Replaced the old raw animation-time control with a labeled **Card speed** slider ranging from 0.25× to 2×.
- Stored the selected speed locally so it persists between sessions.
- Applied the setting only to client presentation delays and animation durations; it does not change game rules, effect ordering, targeting, or server-side resolution.
- Kept the control inside the normal right-side hover drawer.
- Added a **Settings** edge label while the drawer is closed and hide that label while the drawer is visible.

## Validation coverage

- Added regression tests for fixed-value distributed targeting, repeat-target maximum calculation, and low-availability target pools.
- Added regression coverage for Shadowcat selecting a zero-threat side scheme.
- Added regression tests for shared resource-cost reduction and Uncanny X-Men controller scoping.
- Audited all retained campaign card scripts and the Synthezoid Smackdown, Wonder Man, and Hercules implementations against their final card text and engine conventions.

## Distribution changes

- Added a reproducible Windows release script and PyInstaller specification with dynamic card-module discovery.
- Added a GitHub Actions workflow that builds the Windows archive on demand or for `v*` tags.
- Added an explicit packaging allowlist, SHA-256 generation, release manifest, attribution, and release checklist.
- Included required sounds and interface textures in the repository while continuing to exclude downloaded card scans, optional offline images, saves, statistics, crash logs, virtual environments, and generated build output.
