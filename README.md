# Marvel LCG Digital — Community Build

This community-maintained build is based on [Marvel LCG Digital](https://irefrixs.itch.io/marvel-lcg), originally developed by the Irefrixs Team. It adds campaign support, community content, gameplay corrections, and interface improvements while keeping the game free to play.

The upstream developers have given permission for modified builds to be published while they finalize a permissive software license. See [ATTRIBUTION.md](ATTRIBUTION.md) for project and intellectual-property notices.

## Latest testing release: v1.2.0

[Download Community Build v1.2.0 for Windows](https://github.com/sdolle1775/marvel-lcg/releases/tag/v1.2.0)

This prerelease's featured content is **Daredevil** and **Echo**, now fully playable as the two **Fear No Evil** heroes. Both include starter decks, complete identity-specific cards, obligations, and registered nemesis sets; Daredevil also uses the separate Sense deck, while Echo can tuck and replay events through Watch and Learn and Photographic Reflexes. The release also completes the **Age of Apocalypse** campaign rules and tracking and updates core behavior for Rules Reference v1.8. Major changes include:

- Fully playable Daredevil and Echo hero expansions, starter decks, signature cards, obligations, and nemesis sets.
- Daredevil's Sense deck and Echo's tucked-event mechanics, together with the remaining Fear No Evil player cards and Starting abilities.
- Corrected Daredevil and Echo interactions: Improvisation resolves every matching event trait without exhausting, and Enhanced Olfaction triggers when another effect removes the last threat from the main scheme.
- Team-Up ally replacement and restriction validation now support non-event Team-Up cards such as Dance with the Devil.
- Complete Age of Apocalypse campaign setup, missions, Prelates and Overseers, rewards, outcomes, persistent health, and campaign-log tracking.
- Rules Reference v1.8 surge timing, improved multi-villain targeting, alternate-cost support, campaign-log save controls, and reusable modular-difficulty setup.
- Corrected ordered-deck presentation, card-preview click handling, max-one-per-player limits, obligation choices, attack targeting, and numerous card and scenario interactions.

Campaign setup choices are saved in `campaign_settings.json`. When installing a new release, extract it into a new folder and copy this file from the previous installation to preserve those choices. Also copy any saves, replays, or custom decks you want to retain. Keep `marvel-lcg.exe` beside its `_internal` folder, and do not copy the old executable or old `public`, `data`, or cache folders into the new installation.

See the [complete patch notes](PATCH_NOTES.md) and [installation guide](docs/install_guide.md) for details.

## Antivirus scan and Windows packaging

v1.2.0 uses the byte-matched Python 3.12.13 runtime, pinned release dependencies, PyInstaller one-folder package, UPX-disabled configuration, and hash-verified locally compiled bootloader from v1.1.1. The one-folder layout avoids self-extracting the executable into a temporary directory and reduces generic heuristic antivirus detections.

The package remains unsigned. During release testing, the v1.2.0 executable passed a local Microsoft Defender custom scan, but Microsoft's engine on VirusTotal subsequently flagged the same file; the [VirusTotal report for the released executable](https://www.virustotal.com/gui/file/b434e1c5fe1d916fe2fa9af4b90289b3a72058a078e3f531d732083def559ad4/detection) is public. Detection results can change over time, so this remains an unresolved antivirus warning rather than a guarantee that every scanner will accept the build. A SHA-256 checksum file is generated beside the Windows archive so testers can verify the exact download.

## Community build highlights

- **Campaigns:** Complete playable campaign flows for **Mutant Genesis**, **NeXt Evolution**, **Age of Apocalypse**, **Agents of S.H.I.E.L.D.**, **Galaxy's Most Wanted**, and **The Mad Titan's Shadow**.
- **Playable heroes:** Full **Wonder Man**, **Hercules**, **Daredevil**, and **Echo** hero expansions, each with a starter deck, identity-specific cards, an obligation, and a registered nemesis set. Daredevil includes his separate Sense deck, while Echo includes her tucked-event mechanics.
- **Player cards:** The complete **Fear No Evil** player-card set, including Starting and Team-Up cards, together with the aspect and basic player cards released alongside Wonder Man and Hercules.
- **Synthezoid Smackdown:** Standard and expert cooperative scenarios against **She-Hulk** and **Vision**, supported by the S.H.I.E.L.D. Ops, Thunderbolts, Taskmaster, Deadly Duo, Young Avengers, Scarlet Twins, Moon Knight, and Royal Guard encounter sets.
- **Trickster Takeover:** Complete standard and expert **Loki: God of Lies** scenarios, including the Loki Avatar stages, Synergy environments, Shatter the Illusion, and Trickster Magic content.
- **Civil War:** Expert scenario variants for **Iron Man**, **Captain Marvel**, **Captain America**, and **Spider-Woman**.
- Campaign implementations cover setup, progression, campaign logs, persistent health and cards, player assignments, missions, evidence, rewards, and campaign-specific scenario changes.
- Rules and card-engine implementations support the added content's Starting abilities, Rules Reference v1.8 Team-Up ally replacement, multi-villain targeting, alternate resource costs, and reusable modular-difficulty setup.
- The community content is registered throughout the card database, starter-deck library, scenario loader, encounter-set system, and campaign framework for play alongside the original Irefrixs content.

## Release and distribution

- [GitHub releases](https://github.com/sdolle1775/marvel-lcg/releases)
- [Release build and publishing guide](docs/release_guide.md)
- Standard card artwork is downloaded from the image servers configured in `launch.json` and cached locally. Downloaded card images are not included in the main release archive.
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

![](/docs/assets/image-1.jpg)
![](/docs/assets/image-2.jpg)
