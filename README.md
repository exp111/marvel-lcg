# Marvel LCG Digital — Community Build

This community-maintained build is based on [Marvel LCG Digital](https://irefrixs.itch.io/marvel-lcg), originally developed by the Irefrixs Team. It adds campaign support, community content, gameplay corrections, and interface improvements while keeping the game free to play.

The upstream developers have given permission for modified builds to be published while they finalize a permissive software license. See [ATTRIBUTION.md](ATTRIBUTION.md) for project and intellectual-property notices.

## Latest release: v1.3.3.1

[Download Community Build v1.3.3.1 for Windows](https://github.com/sdolle1775/marvel-lcg/releases/tag/v1.3.3.1).

v1.3.3.1 replaces on-demand card-image downloads with a verified, persistent local artwork library. The application **automatically downloads card images and stores them locally on the host computer**. The application ZIP stays small: the host prepares the approximately **1.7 GiB** collection separately before first play, then reuses it across restarts and application updates. LAN and Cloudflare players receive images from the host. Open **Card artwork** on the main menu for progress, recovery controls and library maintenance instructions. The main menu and Credits display **Community Build v1.3.3.1r**.

The hotfix also adds the default-off **Remove Standard Set Restriction** option and preselects sole eligible response prompts while still requiring confirmation. See the [release summary](docs/releases/v1.3.3.1.md), [complete patch notes](PATCH_NOTES.md), and [installation and artwork maintenance guide](docs/install_guide.md#6-card-images).

**Antivirus notice:** The [VirusTotal report for this executable](https://www.virustotal.com/gui/file/8277bb66d2a228c6c6c10f23e599184889e04a5a5be044944c8b63de7788794e?nocache=1) reports Microsoft and SecureAge detections as of October 11, 2026, despite the earlier clean local Defender scan. Review the warning in the release summary before running the package. A connection to the artwork changes is unconfirmed.

### Included from earlier releases

v1.3.3 added a complete local replay library with playback that stops at the recording's endpoint, restored optional discard and Psi-Weapon choices, corrected card and scenario timing, restored the sparkles animation, and updated community credits. It also fixed form-change entry triggers, upgrade discounts, Victory ordering, Kang's keywords, Purple Man's obligations, Nightcrawler's forced choices, Bulletproof Belle/Tough prevention, Kingpin's side-scheme reveals, and Synth-Suit. This hotfix includes all earlier v1.3 releases and content, including:

- The complete **Fear No Evil** box: Daredevil and Echo, all player cards, five interchangeable Underling villains, five interchangeable scenarios, Kingpin's standalone scenario, all six modular encounter sets, and the full campaign.
- Rules Reference v1.8 simultaneous timing, enabled by default for new games. Interrupts and responses created by one occurrence share the correct timing window and can be resolved in player-chosen order. The legacy timing dispatcher remains available through the Rule settings.
- Updated v1.8 timing for Surge, Incite, Quickstrike, Teamwork, Toughness, Retaliate, Vulnerable, Villainous, Victory, When Defeated, When Completed, and related attack/damage workflows.
- A new optional **Show Deck During Full Search** setting, allowing players to inspect the complete searched deck or discard pile while still preserving random searches and shuffles.
- A dedicated Fear No Evil campaign setup interface for tracking scenario outcomes, Underlings, campaign cards, rewards, removed allies and Persona supports, and randomized scenario progression.

Campaign setup choices are saved in `campaign_settings.json`. When installing a new release, extract it into a new folder and copy this file from the previous installation to preserve those choices. Also copy any saves, replays, custom decks, and explicit local artwork overrides you want to retain. Artwork-enabled builds automatically reuse the persistent user artwork library across installations; see the [artwork migration instructions](docs/install_guide.md#6-card-images). Keep `marvel-lcg.exe` beside its `_internal` folder, and do not copy the old executable or old `public` or `data` folders into the new installation.

See the [complete patch notes](PATCH_NOTES.md) and [installation guide](docs/install_guide.md) for details.

## Windows packaging

v1.3.3.1 uses the established v1.3.2/v1.3.3 release environment: Python 3.12.13, the same pinned dependencies and verified locally compiled bootloader, PyInstaller's one-folder package with an embedded Python module archive, and UPX disabled. The one-folder layout avoids extracting the executable into a temporary directory at startup.

Verify the downloaded archive with its accompanying `.sha256` file.

## Community build highlights

Jessica Jones and Luke Cage are available in the current source build. The published v1.3.3.1 executable predates these two packs.

- **Campaigns:** Complete playable campaign flows for **Fear No Evil**, **Mutant Genesis**, **NeXt Evolution**, **Age of Apocalypse**, **Agents of S.H.I.E.L.D.**, **Galaxy's Most Wanted**, and **The Mad Titan's Shadow**.
- **Playable heroes:** Full **Wonder Man**, **Hercules**, **Daredevil**, **Echo**, **Jessica Jones**, and **Luke Cage** hero expansions, each with a starter deck, identity-specific cards, an obligation, and a registered nemesis set. Daredevil includes his separate Sense deck, while Echo includes her tucked-event mechanics. Jessica Jones and Luke Cage include their complete player-card packs and reviewed Hall of Heroes artwork, with six documented reprint matches.
- **Player cards:** The complete **Fear No Evil** player-card set, including Starting and Team-Up cards, together with the aspect and basic player cards released alongside Wonder Man, Hercules, Jessica Jones and Luke Cage.
- **Fear No Evil scenarios:** Five interchangeable Underlings—**Bullseye**, **Electro**, **Hammerhead**, **Purple Man**, and **Typhoid Mary**—can be paired with **Art Museum Heist**, **The Getaway**, **Protection Racket**, **The Raft Breakout**, or **Stop the Presses!**. **Kingpin** is implemented as a complete standalone scenario, together with the Disasters, Cops, Drive, The Owl, Tombstone, and Tracksuit Mafia modular sets.
- **Synthezoid Smackdown:** Standard and expert cooperative scenarios against **She-Hulk** and **Vision**, supported by the S.H.I.E.L.D. Ops, Thunderbolts, Taskmaster, Deadly Duo, Young Avengers, Scarlet Twins, Moon Knight, and Royal Guard encounter sets.
- **Trickster Takeover:** Complete standard and expert **Loki: God of Lies** scenarios, including the Loki Avatar stages, Synergy environments, Shatter the Illusion, and Trickster Magic content.
- **Civil War:** Expert scenario variants for **Iron Man**, **Captain Marvel**, **Captain America**, and **Spider-Woman**.
- Campaign implementations cover setup, progression, campaign logs, persistent health and cards, player assignments, missions, evidence, rewards, and campaign-specific scenario changes.
- Rules and card-engine implementations support default-on Rules Reference v1.8 timing, Starting abilities, Team-Up ally replacement, multi-villain targeting, alternate resource costs, and reusable modular-difficulty setup.
- The optional full-deck-search display exposes all cards in a complete search without changing random selection, shuffle, or hidden-information behavior when the option is disabled.
- The community content is registered throughout the card database, starter-deck library, scenario loader, encounter-set system, and campaign framework for play alongside the original Irefrixs content.

## Release and distribution

- [GitHub releases](https://github.com/sdolle1775/marvel-lcg/releases)
- [Release build and publishing guide](docs/release_guide.md)
- v1.3.3.1 prepares reviewed artwork packs in a persistent user library, separate from the application archive. See the [artwork installation and maintenance instructions](docs/install_guide.md#6-card-images). The published v1.3.3 executable retains its original artwork downloader.
- The release build includes the small sounds, card backs, status cards, placeholders, and set textures required by the interface.

## Documentation

| Guide | Description |
| --- | --- |
| [Install Guide](docs/install_guide.md) | How to install and run the game |
| [How to Play](https://itch.io/t/3763917/how-to-play-this-game) | Game rules and controls |
| [Card Scripting Guide](docs/card_scripting_guide.md) | How to write card ability scripts |
| [Engine Architecture](docs/engine_architecture.md) | Engine internals for developers |
| [Debug Guide](docs/debug_guide.md) | How to debug the game |
| [Editor Guide](docs/editor_guide.md) | How to use the card editor |
| [Release Guide](docs/release_guide.md) | How to validate and package a release |

## Security warning

This game runs Python card scripts. Do not install or run third-party card scripts unless you trust their source.

这个游戏会运行用 Python 编写的卡牌脚本。除非你完全信任其来源，否则不要安装或运行任何第三方卡牌脚本。

## Screenshots

**Main menu — Community Build v1.3.3.1r**

![Current main menu with game setup, replay library, deck editor, card browser, and artwork controls](/docs/assets/image-1.jpg)

**Two-player hotseat — round six**

Daredevil and Echo face Typhoid Mary in The Raft Breakout, with both players' upgrades and supports in play.

![Two-player hotseat game showing Daredevil and Echo's developed board against Typhoid Mary](/docs/assets/image-2.jpg)
