# Marvel Champions Digital v1.1.1

Application version: **1.1.1r**
Windows file version: **1.1.1.0**

This release contains the corrections completed after v1.1.0. The full v1.1.0 release description is appended below so this file remains a cumulative description of the build.

## Changes since v1.1.0

### Trickster Takeover

- Enchantress I now places a charm counter after she attacks, matching her printed forced response.
- **Stories and Lies** now preserves Loki's current remaining hit points when swapping to another physical Avatar card. Attached **Intense Focus** and **Total Focus** modifiers are reapplied once to the new Avatar's maximum hit points without duplicating the bonus.
- Loki's Synergy environments now add their printed 4 damage or 4 threat removal to the attack or thwart event itself, so the bonus resolves correctly with defenses and other event modifiers.
- Corrected the printed Crisis and Acceleration icons on the affected Loki side schemes.

### Deck importing and interface

- MarvelCDB imports now use the returned identity card code instead of relying only on the shared hero name. This distinguishes T'Challa from Shuri for **Black Panther** decks and Peter Parker from Miles Morales for **Spider-Man** decks.
- Identity-code imports no longer emit a false missing-file warning before resolving the matching starter template.
- **Blindfold** and other ordered encounter-card selections now preserve the displayed encounter-deck order when cards are returned.
- Attack-card animation cleanup no longer allows a pending browser animation frame to reapply a movement transform after the animation has already completed.

### Targeting and stability

- Forced abilities on player-assigned obligations now resolve through the player holding the obligation. This fixes **Protect Humanity** freezing when its villain attack is redirected to an ally.
- Added regression coverage for same-name MarvelCDB identities, Loki Avatar swaps, Synergy bonuses, side-scheme icons, and obligation targeting.

### Build and data integrity

- Regenerated the card-database checksum after the final Trickster Takeover data corrections.
- Release tooling now supports standard, no-archive, and locally compiled PyInstaller bootloader comparison builds.
- This v1.1.1 test package uses the Python 3.12 one-folder layout, disables UPX, excludes developer-only command modules, and uses the locally compiled PyInstaller bootloader flow used for the final v1.1.0 Windows package.

## Windows package verification

The v1.1.1 Windows package uses the locally compiled PyInstaller bootloader build flow.

- Microsoft Defender custom scan: **Undetected**.
- [VirusTotal report for the exact executable](https://www.virustotal.com/gui/file/a650db6b493869fc993206b66e2161f38ea2d19210fe40324c07e16688b29c96?nocache=1): **1/70**, with only SecureAge's generic detection; Microsoft is undetected.
- Executable SHA-256: `a650db6b493869fc993206b66e2161f38ea2d19210fe40324c07e16688b29c96`
- ZIP SHA-256: `672985f0c691f51eb719bef58d1c3b75f652730a9d0f63803630957dd1f979dd`

## Testing and installation

1. Extract the ZIP into a new, empty folder rather than overwriting an older installation.
2. Copy `campaign_settings.json` from the previous build if you want to retain campaign setup choices.
3. Copy any personal saves, replays, or custom decks you want to test. Do not copy the old executable, `public`, `data`, `assets/cache`, or `launch.json`.
4. Smoke-test both a new game and an existing save before relying on the build for a longer campaign.

---

# Marvel Champions Digital v1.1.0

Application version: **1.1.0r**
Windows file version: **1.1.0.0**

## New content

### Trickster Takeover

- Added the complete **Loki: God of Lies** scenario in standard and expert modes.
- Implemented Loki's Avatar stages, Synergy environments, encounter cards, setup flow, and the **Trickster Magic** modular set.
- Added **Shatter the Illusion** to the visible out-of-play area and implemented its Shatter-counter damage resolution, including compatibility for saves created during development.

### Civil War

- Completed the expert versions of the **Iron Man**, **Captain Marvel**, **Captain America**, and **Spider-Woman** villain scenarios.
- Added the missing stage III/IV data and linked those stages to the matching scripted leader behavior.
- Completed missing Civil War card data and scripting coverage.

## Fixes and improvements

- Standard and Expert encounter-set variants now replace the scenario default instead of combining multiple Standard or Expert decks. Setup can also switch cleanly between variants.
- Versioned browser startup and menu navigation prevent an older cached menu or setup page from replacing the interface bundled with the running executable.
- Fixed crashes reported while starting Enchantress games and while resolving Taskmaster's Sword against attached characters.
- Two-Gun Kid must now choose a different enemy for the additional attack and cannot apply both attacks to the same target.
- Corrected Groot and Rocket Raccoon's hero/alter-ego image-side mappings when loading artwork from Cerebro.
- Improved scenario/save migration behavior for newly completed content and corrected Loki's Shatter-counter damage total.

## Previously included from the v1.0 releases

v1.1.0 also contains all earlier community-build work: the Mutant Genesis, NeXt Evolution, Age of Apocalypse, Agents of S.H.I.E.L.D., Galaxy's Most Wanted, and The Mad Titan's Shadow campaign flows; the Wonder Man and Hercules hero expansions; Synthezoid Smackdown scenarios and modular sets; persistent campaign settings; Cerebro-first card artwork loading; community menu branding; release packaging hardening; browser cache protections; and the accumulated card, campaign, encounter, targeting, and save-compatibility corrections from v1.0.0 through v1.0.0.5.

## Windows package verification

The Windows package was rebuilt from the same v1.1.0 source using a locally compiled PyInstaller bootloader. The public filename and application version remain unchanged.

- Microsoft Defender: **Undetected**.
- [VirusTotal report for the exact executable](https://www.virustotal.com/gui/file/625968a692a3e4da861c4c6d2f90317335ee5c3e8976b72dcc111d3c41446176?nocache=1): **1/71**, with only SecureAge's generic detection; Microsoft is undetected.
- Executable SHA-256: `625968a692a3e4da861c4c6d2f90317335ee5c3e8976b72dcc111d3c41446176`
- ZIP SHA-256: `f8d03f26c073fb8f048ad8099b23c9b1ca07d162617bc1fd5d85c8a24212f0c1`

## Testing and installation

1. Extract the ZIP into a new, empty folder rather than overwriting an older installation.
2. Copy `campaign_settings.json` from the previous build if you want to retain campaign setup choices.
3. Copy any personal saves, replays, or custom decks you want to test. Do not copy the old executable, `public`, `data`, `assets/cache`, or `launch.json`.
4. Smoke-test both a new game and an existing save before relying on the build for a longer campaign.

This is a community-maintained build based on the Irefrixs Team project. Card artwork remains excluded from the main package and is downloaded using the image servers configured in `launch.json`.
