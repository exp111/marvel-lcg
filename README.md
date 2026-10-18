# Marvel LCG Digital — Community Build

## Community build highlights

- **Full campaigns:** Fear No Evil, Mutant Genesis, NeXt Evolution, Age of Apocalypse, Agents of S.H.I.E.L.D., Galaxy's Most Wanted, and The Mad Titan's Shadow, with setup, progression, campaign logs, rewards, persistent cards and health, and campaign-specific rules.
- **New heroes:** Wonder Man, Hercules, Daredevil, Echo, Jessica Jones, and Luke Cage, including starter decks, signature cards, obligations, nemesis sets, and their accompanying aspect and basic cards.
- **Rules Reference v1.8:** Default-on simultaneous timing with player-chosen interrupt and response order, updated keywords, and corrected attack, damage, defeat, and completion timing. Legacy timing remains selectable.
- **Fear No Evil:** The complete box, with five interchangeable Underlings and five scenarios, standalone Kingpin, six modular sets, and dedicated campaign tracking.
- **Synthezoid Smackdown:** Standard and expert cooperative She-Hulk and Vision scenarios, plus all eight modular encounter sets.
- **Trickster Takeover:** Standard and expert Loki: God of Lies scenarios, Loki Avatars, Synergy environments, Shatter the Illusion, and Trickster Magic.
- **Civil War modularity:** Separate leader and scheme selection for Civil War and Synthezoid Smackdown, shared Registration/Resistance pools covering all 20 main schemes, preconstructed defaults, and faction-based random modular selection.
- **Reliable artwork:** Automatically downloaded, verified card images supported through Luke Cage. The persistent library survives updates, works offline once prepared, and supplies images to LAN and Cloudflare players.
- **Replay and setup tools:** A local replay library, playback controls and recovery, saved campaign setup, optional unrestricted Standard/Expert sets, and full-deck search previews.
- **Gameplay improvements:** Expanded multiplayer targeting, Starting and Team-Up abilities, alternate costs, and card-text, timing, payment, and interaction fixes across heroes and scenarios.

## Latest release: v1.3.4

[Download Community Build v1.3.4 for Windows](https://github.com/sdolle1775/marvel-lcg/releases/tag/v1.3.4).

This release adds Jessica Jones and Luke Cage, reworks Civil War and Synthezoid Smackdown setup, and fixes card and scheme interactions. The main menu and Credits display **Community Build v1.3.4r**. See the [v1.3.4 changes](docs/releases/v1.3.4.md) or [complete patch notes](PATCH_NOTES.md).

## Installing and updating

- Extract the ZIP into a **new folder** and keep `marvel-lcg.exe` beside its `_internal` folder.
- Copy `campaign_settings.json` from the previous installation to preserve campaign setup choices. Also copy personal saves, replays, custom decks, and artwork overrides you want to keep. Keep the new executable, `public`, and `data` folders.
- Open **Card artwork** from the main menu for preparation progress, Pause, Resume, Retry, and library maintenance. The approximately **1.7 GiB** collection downloads separately before first play; updates reuse verified artwork and download only missing or changed packs.
- Keep the persistent artwork library in place, or retain the same custom `artwork_folder` setting. See the [installation and artwork guide](docs/install_guide.md#6-card-images).

## Windows packaging

Uses the established Python 3.12.13 release environment, pinned dependencies, verified custom bootloader, and PyInstaller one-folder layout with UPX disabled. Verify the ZIP against its accompanying `.sha256` file. The published executable matches the [v1.3.4 VirusTotal report](https://www.virustotal.com/gui/file/20d9c8682195c20f52cbd4674d6d118362b178f0973b3552a0f8ceffab871413?nocache=1).

## About this build

This free community-maintained build is based on [Marvel LCG Digital](https://irefrixs.itch.io/marvel-lcg), originally developed by the **Irefrixs Team**. Community build maintenance: **Sam (sdolle1775)**.

The upstream developers have given permission for modified builds to be published while they finalize a permissive software license. See [ATTRIBUTION.md](ATTRIBUTION.md) for project, artwork, and intellectual-property notices.

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
