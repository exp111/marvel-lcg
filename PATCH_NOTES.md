# Marvel Champions Digital v1.1.0

Application version: **1.1.0r**
Windows file version: **1.1.0.0**

This testing build contains the first feature release after v1.0.0.5. The package keeps the normal v1.1.0 filename and version; it can be marked as a prerelease on GitHub while public testing is in progress.

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
- Forced abilities on player-assigned obligations now resolve through that player, fixing Protect Humanity freezes when redirecting a villain attack to an ally.
- Corrected Groot and Rocket Raccoon's hero/alter-ego image-side mappings when loading artwork from Cerebro.
- Improved scenario/save migration behavior for newly completed content and corrected Loki's Shatter-counter damage total.

## Previously included from the v1.0 releases

v1.1.0 also contains all earlier community-build work: the Mutant Genesis, NeXt Evolution, Age of Apocalypse, Agents of S.H.I.E.L.D., Galaxy's Most Wanted, and The Mad Titan's Shadow campaign flows; the Wonder Man and Hercules hero expansions; Synthezoid Smackdown scenarios and modular sets; persistent campaign settings; Cerebro-first card artwork loading; community menu branding; release packaging hardening; browser cache protections; and the accumulated card, campaign, encounter, targeting, and save-compatibility corrections from v1.0.0 through v1.0.0.5.

## Testing and installation

1. Extract the ZIP into a new, empty folder rather than overwriting an older installation.
2. Copy `campaign_settings.json` from the previous build if you want to retain campaign setup choices.
3. Copy any personal saves, replays, or custom decks you want to test. Do not copy the old executable, `public`, `data`, `assets/cache`, or `launch.json`.
4. Smoke-test both a new game and an existing save before relying on the build for a longer campaign.

This is a community-maintained build based on the Irefrixs Team project. Card artwork remains excluded from the main package and is downloaded using the image servers configured in `launch.json`.
