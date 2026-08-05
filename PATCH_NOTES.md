# Release 1.0 patch set

Application version: **1.0.0.1r**

Baseline: Irefrixs Team upstream `master` at `a77154a`

These notes compare the final community release with the original upstream release. Development-only corrections to campaigns and content packs introduced by this release are represented by their final features, not listed as separate fixes. Superseded and reverted implementations are omitted.

## Highlights

- Added complete digital campaign flows for **Mutant Genesis**, **NeXt Evolution**, **Age of Apocalypse**, **Agents of S.H.I.E.L.D.**, **Galaxy's Most Wanted**, and **The Mad Titan's Shadow**.
- Added the **Wonder Man** and **Hercules** hero expansions, including starter decks, hero cards, obligations, and nemesis content.
- Added the **Synthezoid Smackdown** cooperative content, including She-Hulk and Vision scenarios and eight modular encounter sets.
- Added an adjustable card-interaction speed setting that changes presentation timing without changing game-state resolution.
- Incremented the application build and disabled browser caching for scene-setup metadata so updated scenarios, heroes, and encounter sets appear after installing a new release.
- Corrected fixed-total threat and damage selection, attached-identity restrictions, and several card scripts present in the original release.

## Campaign support

- Added a campaign selector with stable internal campaign identifiers so campaign setup, logs, replay data, and saved state select the intended campaign reliably.
- Retained selection support for **The Rise of Red Skull** and **Sinister Motives** alongside the six newly implemented campaign flows.
- Added campaign-log card previews with a fixed, readable tooltip size and position.
- Added campaign-specific setup screens, scenario progression, persistent rewards and penalties, campaign pools, and scenario-dependent setup instructions.
- Added persistent remaining-hit-point setup fields for each selected player. Recorded values can be used in standard or expert campaigns; Age of Apocalypse retains its matching option to place 3 threat on the mission and heal to full whenever this feature is used.
- Added Mutant Genesis role and reward content for **Brawler**, **Commander**, **Defender**, and **Peacekeeper**, plus campaign player side schemes and the complete Magneto campaign-card behavior, including flipped permanents and attachments.
- Added the NeXt Evolution campaign player side schemes and their scenario-specific setup and persistence rules.
- Added Age of Apocalypse campaign missions, mission allies, overseers, resource matching, mission attempts, campaign setup choices, and campaign upgrades.
- Added Agents of S.H.I.E.L.D. campaign progression, evidence, Board Member attachment and loss conditions, Executive Board state, and scenario setup choices.
- Added Galaxy's Most Wanted credits, market purchases and discards, ship upgrades, market-card abilities, and scenario progression.
- Added The Mad Titan's Shadow campaign cards, flipped-permanent placement, scenario progression, and campaign state used across its five scenarios.

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
- Corrected Atonement so Hercules readies through the standard ready operation and receives the optional alter-ego form change after a Gift's enter-play response resolves.
- Corrected Protect Humanity so a villain attack checks the assigned player's allies and presents the required redirection target instead of treating the villain as the player.
- Corrected Son of Zeus so its Hercules and identity-specific upgrade ready effects use the supported ready operation.
- Added the set image and card-database registration.

## Existing-release gameplay and card corrections

- Corrected **Creative Solution** so a purchased market card is discarded rather than removed from the game.
- Corrected **Close Call** to use Hero Interrupt timing.
- Prevented **Badoon Headhunter** from prompting for a random discard when the affected player's hand is empty.
- Corrected Sinister Motives S.H.I.E.L.D. Tech ownership and stat application, basic-thwart restrictions, the correct side of **Shock Knuckles** receiving its ATK bonus, and empty-hand handling for **Back Alley Burglary**.
- Corrected **Improved Recovery Upgrade** from The Rise of Red Skull so using its recovery bonus exhausts the upgrade.
- Corrected scenario creation so locked, mandatory encounter sets cannot be deselected in the setup interface and are restored server-side if omitted from the submitted selection.

### Card data corrections

- Added the printed one-per-enemy limit to **Concussive Blow**.
- Corrected punctuation in **Defy Danger**.
- Added the printed unit cost of 5 to **Onrush**.
- Corrected **North American Sea Wall** to Victory 2.
- Added Incite 1 to both resource sides of **A.I.M. Interference**.
- Corrected the spelling of Aggression in **Authority**.
- Regenerated the card-database checksum after the final data changes.

### Threat and damage distribution

- Added an exact-up-to-available target range for effects that distribute a fixed total. Players must now allocate the full legal amount while still being allowed to resolve an effect when fewer valid threat or health points exist.
- Corrected distributed selection for the original-release cards **Gunboat Diplomacy**, **Mutant Peacekeepers**, **Torrential Rain**, **Inconspicuous**, and **Giant Help**.
- Corrected **Mutant Peacekeepers** so its final threat value is calculated after choosing and exhausting participating X-Men allies.
- **Shadowcat** can now select a side scheme with zero threat when placing threat through her response.

### Attack and condition interactions

- Corrected attached-identity defense restrictions so they bind to the attached player instead of being interpreted as a card finder. This prevents attack windows from suppressing or breaking otherwise legal identity abilities, including Nightcrawler interactions.

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

## Distribution changes

- Added a reproducible Windows release script and PyInstaller specification with dynamic card-module discovery.
- Added a GitHub Actions workflow that builds the Windows archive on demand or for `v*` tags.
- Added an explicit packaging allowlist, SHA-256 generation, release manifest, attribution, and release checklist.
- Included required sounds and interface textures in the repository while continuing to exclude downloaded card scans, optional offline images, saves, statistics, crash logs, virtual environments, and generated build output.
