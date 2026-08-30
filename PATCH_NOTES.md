# Marvel Champions Digital v1.3.0

Application version: **1.3.0r**
Windows file version: **1.3.0.0**

This release completes **Fear No Evil**, adds its full campaign, and makes the new Rules Reference v1.8 timing workflow the default for new games. These notes describe changes since v1.2.0.1.

## Complete Fear No Evil expansion

- Completed the **Fear No Evil** box: the **Daredevil** and **Echo** hero expansions, their obligations and nemesis sets, the complete player-card pool, every scenario and encounter set, and all campaign cards.
- Added standard and expert versions of the five interchangeable Underling villains: **Bullseye**, **Electro**, **Hammerhead**, **Purple Man**, and **Typhoid Mary**.
- Added the five interchangeable scenarios: **Art Museum Heist**, **The Getaway**, **Protection Racket**, **The Raft Breakout**, and **Stop the Presses!**, including their scenario-specific setup and encounter mechanics.
- Added **Kingpin** as a complete standalone standard/expert scenario with its built-in scenario setup. Selecting Kingpin disables the interchangeable scenario and Standard-set choices that do not apply to him.
- Added all six modular encounter sets in printed order: **Disasters**, **Cops**, **Drive**, **The Owl**, **Tombstone**, and **Tracksuit Mafia**.
- Implemented the complete Fear No Evil campaign, including scenario and Underling selection, scenario results, campaign-card setup, persistent campaign tracking, rewards, removed allies and Persona supports, and campaign-specific scenario instructions.
- Added campaign helpers that randomly offer up to two unfinished scenarios and an unused Underling while keeping completed, failed, and previously selected entries out of those results.

## Rules Reference v1.8 timing

- Added `v18_timing`, enabled by default for new games. Interrupts and responses created by the same attack, damage, defeat, defense, basic-power, recovery, threat, or scheme occurrence now share the correct timing window and can be resolved in player-chosen order.
- Players can choose among simultaneous forced abilities at the same priority. Optional response opportunities rotate from the first player and are recalculated after each resolution, allowing newly legal responses—such as Jarnbjorn after Nova readies Supernova Helmet—to be used in the same window.
- Updated Retaliate, Vulnerable, consequential damage, When Defeated, and When Completed to use their printed v1.8 priorities and lifecycle timing.
- Updated Incite, Quickstrike, Restricted, Surge, Teamwork, Temporary, Toughness, Victory, and Villainous to initiate at their printed timing points. Surge and Incite are cancellable When Revealed effects, reveal responses wait until the complete reveal finishes, Ranged prevents Retaliate, and Piercing does not discard Tough when an attack would deal no damage.
- Hardened nested timing occurrences, replay identities, unnamed internal effects, duplicate candidates, target/cost revalidation, and parent/child attack and damage windows.
- Constant modifiers and other non-triggered game-state effects apply automatically without unnecessary ordering prompts. Exact one-target outcomes are preselected where safe, while defense declarations and Ask abilities retain explicit confirmation.
- Preserved the prior message-by-message dispatcher as an optional legacy mode. Disabling `v18_timing` changes only simultaneous-trigger handling and does not disable separately selected v1.6 rulings.
- Existing saves and replays created before v1.3.0 continue in legacy timing unless they explicitly contain the v1.8 timing rule, preserving their recorded prompt order.

## Interface and search improvements

- Added the optional **Show Deck During Full Search** rule. When enabled, a complete deck or discard-pile search displays every card being searched so the player can inspect the full pool before choosing.
- Kept random full-deck searches random even while the deck is visible; the last inspected or selected card is no longer incorrectly reused as the random result.
- Full-search presentation works for player and encounter searches while preserving shuffle behavior, card-order rules, and the original hidden presentation when the option is disabled.
- Improved campaign setup presentation and status tracking, including visible delimiter tokens for removed allies and Persona supports and cleaner completed/failed controls.
- Removed redundant one-of-one target prompts where the outcome is deterministic. Ask remains an explicit option even when it is the only action available on a selectable player card.

## Scenario and engine corrections

- Restricted each **Protection Racket** main scheme to its assigned player for player-initiated thwart effects while preserving scenario effects that must add or remove threat across personal schemes.
- Corrected crisis handling across Protection Racket's separate main schemes.
- Corrected Art Museum Heist attachment setup, search, shuffling, action labels, and full-search randomization.
- Corrected Underling, modular-set, Kingpin, and campaign-card values, selectors, timing, targets, status effects, empty-search fallbacks, and printed-text interactions found during focused audits.
- Corrected partial and empty full-deck searches such as **Suit Up** so legal results remain selectable without exposing or reusing invalid search state.

## Antivirus notice and Windows package

- The Windows package remains unsigned and uses the pinned Python 3.12.13 runtime, PyInstaller one-folder layout, and UPX-disabled configuration used by prior community releases.
- Microsoft's engine on VirusTotal flags the v1.3.0 executable. The [VirusTotal report for the exact packaged executable](https://www.virustotal.com/gui/file/a1ab2e6a911db3c1c2dfefb88a2b8cb145b80542ad31075c6bfcf64959bc452b?nocache=1) is public and should be treated as an unresolved antivirus warning; detection results can change over time.
- The executable in that report has SHA-256 `a1ab2e6a911db3c1c2dfefb88a2b8cb145b80542ad31075c6bfcf64959bc452b`. The release ZIP has its own accompanying `.sha256` file for download verification.

---

# Marvel Champions Digital v1.2.0.1

Application version: **1.2.0.1r**
Windows file version: **1.2.0.1**

This hotfix contains corrections made after v1.2.0.

## Hotfix fixes

- Corrected Nebula's encounter Techniques so only the first Technique attachment revealed each round gains surge, rather than the first one revealed to every player.
- Corrected **Brainstorm** so Patrol or another effect that prevents threat removal does not prevent the event from being played or resolving its remaining instructions.
- Corrected **In Harm's Way** so it can be played when either its damage portion has a legal enemy or its threat-removal portion has a legal scheme. Because the event is both an attack and a thwart, Confused cancels its entire effect under Rules Reference v1.8.
- Corrected Daredevil's printed THW from 1 to 2. Sense responses and interrupts that say “you” now require Daredevil's identity to make the attack, thwart, threat removal, or defeat, so ally attacks and thwarts cannot trigger cards such as **Radar Sense**.
- Corrected Sense cards leaving play so replacement effects preserve their requested deck position and return those cards to the bottom of the Sense deck instead of its top.
- Corrected Echo's **Photographic Reflexes** flow. A playable event tucked under Echo is selected directly in hero form, the player chooses and discards a viable copy of Photographic Reflexes before payment, that discarded copy cannot pay for the event, and any remaining copies retain their printed resources for normal payment.

The packaged executable passed a local Microsoft Defender custom scan, and its [VirusTotal analysis](https://www.virustotal.com/gui/file/9f526791102675fbdf201d1f039f0e2f4eb84ab1e747b0c7a3f9f7d4cf5eb24c) reported no detections at release time.

---

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

## Testing and installation

1. Extract the ZIP into a new, empty folder rather than overwriting an older installation.
2. Copy `campaign_settings.json` from the previous build if you want to retain campaign setup choices.
3. Copy any personal saves, replays, custom decks, or campaign logs you want to test. Do not copy the old executable, `public`, `data`, `assets/cache`, or `launch.json`.
4. Smoke-test both a new game and an existing save before relying on the build for a longer campaign.

This is a community-maintained build based on the Irefrixs Team project. Card artwork remains excluded from the main package and is downloaded using the image servers configured in `launch.json`.
