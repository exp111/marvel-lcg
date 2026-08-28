# Marvel Champions Digital v1.2.0

Application version: **1.2.0r**
Windows file version: **1.2.0.0**

This description contains only changes made after v1.1.1.

## Featured heroes: Daredevil and Echo

- Added fully playable **Daredevil** and **Echo** heroes from **Fear No Evil**, each with a starter deck, complete identity-specific cards, an obligation, and a registered nemesis set.
- Implemented Daredevil's separate **Sense** deck, Superhuman Senses setup and play rules, Sense attachments, Elektra interactions, and the rest of his hero kit.
- Implemented Echo's **Watch and Learn** tucked-event engine, **Photographic Reflexes**, three-sided upgrades, event-cost interactions, and the rest of her hero kit.
- Added and registered the remaining **Fear No Evil** player cards, including card data, scripts, Starting timing, and Team-Up interactions.
- Corrected **Improvisation** so every matching Attack, Defense, and Thwart trait resolves independently without exhausting the upgrade. Multi-trait events such as **See No Evil, Hear No Evil** can therefore trigger both applicable effects.
- Corrected **Enhanced Olfaction** so it triggers when another effect removes the last threat from the main scheme, including **Living Lie Detector**.

## Campaign support

- Completed the **Age of Apocalypse** campaign rules: mission allies and upgrades, Prelates and Overseers, mission attempts, scenario outcomes, future rewards, card assignment restrictions, and campaign-specific cleanup.
- Completed Age of Apocalypse persistent-health handling for standard and expert campaigns, including defeated-player re-entry, healing choices, and maximum-health limits.
- Corrected Age of Apocalypse setup and campaign-log tracking so scenario choices, mission results, rewards, and player-specific values persist correctly.

## Rules and engine updates

- Updated surge timing to match Rules Reference v1.8.
- Added Rules Reference v1.8 Team-Up ally replacement and now validates Team-Up restrictions before a status card can cancel the associated attack or thwart.
- Generalized Team-Up targeting beyond events so upgrade Team-Up cards such as **Dance with the Devil** load and validate correctly.
- Added complete player-card targeting support for scenarios with multiple villains, including active-villain behavior where required.
- Added support for alternate resource costs such as one matching resource or two resources of any type, including intentional overpayment where a card permits it.
- Enforced printed max-one-per-player limits on Mighty Avengers, Guardians of the Galaxy, Uncanny X-Men, Uncanny X-Force, Children of the Atom, Agents of S.H.I.E.L.D., Flight Squadron, and Heroic Conditioning.
- Added reusable modular-difficulty setup handling for Tower Defense, Project Wideawake, and Infinites.
- Added campaign-log save controls and the matching server operation so campaign progress can be saved from the interface.

## Interface and deck handling

- Added the Fear No Evil set image so Daredevil and Echo display as a proper box selection instead of a gray placeholder in the deck editor.
- Corrected ordered deck-card selection and placement across look-at-deck effects.
- Ordered card rows are now presented right to left to match the resulting deck order.
- Centered card previews no longer intercept clicks intended for selectable cards behind them.
- Deck records now preserve primary and secondary aspects, and Dreadpool setup only treats the actual 'Pool aspect as selecting that encounter content while retaining compatibility with older deck files.

## Card and scenario corrections

- Corrected **Coup de Grace** attack damage.
- Corrected defender-targeted attack effects so boost effects and other responses resolve against the actual defender.
- Corrected obligation choice handling for Ant-Man, Black Panther, Black Widow, Gamora, Hawkeye, Iron Man, Ms. Marvel, Miles Morales, Nebula, Nightcrawler, SP//dr, Spider-Woman, Thor, Winter Soldier, Wolverine, Wasp, and Thunderbolts obligations, together with affected campaign and encounter obligations.
- Corrected Bishop's **Super-Charged** attack bonus and Cyclops's **Lost Visor** attack restriction.
- Corrected defeat rewards for the **Galactic Artifacts** side schemes.
- Corrected **Going Undercover** selection and reorder behavior; Shuri's Black Panther upgrades and **Wakanda Forever!** targeting; core Black Panther's **Vibranium Suit** target requirement; **Rock, Paper, Scissors** resource comparisons; **Dr. Sinclair** and **Godlike Stamina** heal/status choices; and Draugr Buddy's Guard keyword.
- Corrected Enchantress stage threat and **Future of Despair**, Sandman's **City Streets**, **Blackout**, **Blood Debt**, and modular-difficulty setup behavior.
- Corrected alternate-cost behavior for Ironheart, face-bound constant effects, and several scenario setup callbacks.
- Corrected **Machine Man** overpayment, **Norn Stone** stat bonuses on both faces, **Retrieve Odin's Armor**, and affected Vision and resource interactions.
- Corrected Magog/Mojomania modular selection, ratings, and environment completion behavior.
- Corrected Age of Apocalypse mission queries and per-player statistics, Loki stage advancement and **Total Focus**, Baron Zemo, Nebula, Crime, Thanos, and Mad Titan's Shadow campaign reward interactions.

## Windows test package

- Built with the byte-matched Python 3.12.13 runtime and PyInstaller one-folder layout used by v1.1.1.
- Reuses the hash-verified locally compiled PyInstaller bootloader from v1.1.1.
- Pins the complete release dependency graph so later package-index changes cannot silently alter a rebuild.
- UPX is disabled, developer-only command modules are excluded, and card-image cache contents are not bundled.
- A SHA-256 checksum file is generated alongside the archive.
- The released executable passed a local Microsoft Defender custom scan, but Microsoft's VirusTotal engine subsequently flagged the same unsigned file; the exact report is linked from the README and should be treated as an unresolved antivirus warning.

## Testing and installation

1. Extract the ZIP into a new, empty folder rather than overwriting an older installation.
2. Copy `campaign_settings.json` from the previous build if you want to retain campaign setup choices.
3. Copy any personal saves, replays, custom decks, or campaign logs you want to test. Do not copy the old executable, `public`, `data`, `assets/cache`, or `launch.json`.
4. Smoke-test both a new game and an existing save before relying on the build for a longer campaign.

This is a community-maintained build based on the Irefrixs Team project. Card artwork remains excluded from the main package and is downloaded using the image servers configured in `launch.json`.
