# Marvel LCG Digital — Community Build

This community-maintained build is based on [Marvel LCG Digital](https://irefrixs.itch.io/marvel-lcg), originally developed by the Irefrixs Team. It adds campaign support, community content, gameplay corrections, and interface improvements while keeping the game free to play.

The upstream developers have given permission for modified builds to be published while they finalize a permissive software license. See [ATTRIBUTION.md](ATTRIBUTION.md) for project and intellectual-property notices.

## Latest testing release: v1.2.0

[Download Community Build v1.2.0 for Windows](https://github.com/sdolle1775/marvel-lcg/releases/tag/v1.2.0)

This prerelease adds the complete **Fear No Evil** player-card set, completes the **Age of Apocalypse** campaign rules and tracking, and updates core behavior for Rules Reference v1.8. Major changes include:

- Complete Fear No Evil player cards, including Starting abilities and Team-Up ally replacement.
- Complete Age of Apocalypse campaign setup, missions, Prelates and Overseers, rewards, outcomes, persistent health, and campaign-log tracking.
- Rules Reference v1.8 surge timing and Team-Up validation, plus improved multi-villain targeting and alternate-cost support.
- Campaign-log save controls and modular-difficulty setup for Tower Defense, Project Wideawake, and Infinites.
- Correct ordered-deck presentation, card-preview click handling, max-one-per-player limits, obligation choices, attack targeting, and numerous card and scenario interactions.

Campaign setup choices are saved in `campaign_settings.json`. When installing a new release, extract it into a new folder and copy this file from the previous installation to preserve those choices. Also copy any saves, replays, or custom decks you want to retain. Keep `marvel-lcg.exe` beside its `_internal` folder, and do not copy the old executable or old `public`, `data`, or cache folders into the new installation.

See the [complete patch notes](PATCH_NOTES.md) and [installation guide](docs/install_guide.md) for details.

## Antivirus scan and Windows packaging

v1.2.0 uses the byte-matched Python 3.12.13 runtime, pinned release dependencies, PyInstaller one-folder package, UPX-disabled configuration, and hash-verified locally compiled bootloader from v1.1.1. The one-folder layout avoids self-extracting the executable into a temporary directory and reduces generic heuristic antivirus detections.

The package remains unsigned. During release testing, the v1.2.0 executable passed a local Microsoft Defender custom scan, but Microsoft's engine on VirusTotal subsequently flagged the same file; the [VirusTotal report for the released executable](https://www.virustotal.com/gui/file/b434e1c5fe1d916fe2fa9af4b90289b3a72058a078e3f531d732083def559ad4/detection) is public. Detection results can change over time, so this remains an unresolved antivirus warning rather than a guarantee that every scanner will accept the build. A SHA-256 checksum file is generated beside the Windows archive so testers can verify the exact download.

## Community build highlights

- Complete standard and expert **Loki: God of Lies** content from Trickster Takeover, including the Avatar stages, Synergy environments, Shatter the Illusion, and Trickster Magic.
- Complete expert variants for the **Iron Man**, **Captain Marvel**, **Captain America**, and **Spider-Woman** Civil War scenarios.
- Complete campaign flows for **Mutant Genesis**, **NeXt Evolution**, **Age of Apocalypse**, **Agents of S.H.I.E.L.D.**, **Galaxy's Most Wanted**, and **The Mad Titan's Shadow**.
- Complete **Fear No Evil** player-card set with Rules Reference v1.8 Team-Up support.
- New **Synthezoid Smackdown** cooperative scenarios and encounter sets.
- New playable **Wonder Man** and **Hercules** hero expansions with starter decks.
- Campaign setup choices and campaign logs persist locally, with in-game controls for saving campaign-log updates.
- Agents of S.H.I.E.L.D. evidence rewards, Setup abilities, Evidence Seed handling, and persistent Executive Board attachments follow the campaign rules.
- Wonder Man and Hercules include their complete registered nemesis content, with corrected obligation, attack, activation, and fallback-search behavior.
- The latest Trickster Takeover corrections cover Enchantress charms, Loki Avatar health swaps, attached Focus bonuses, Synergy event modifiers, side-scheme icons, and Shatter-counter resolution.
- MarvelCDB imports distinguish same-name identities such as the two Black Panthers and Spider-Men, and identity-code imports no longer produce a false missing-file warning.
- Ordered encounter-card selections preserve their displayed order, and forced player obligations resolve through the player who holds them.
- An adjustable card-interaction speed setting changes presentation timing without affecting gameplay resolution.
- Improved hotseat prompt ownership, card-image loading, browser cache handling, attack-animation cleanup, and card interaction reliability.
- Rules corrections cover fixed-total threat and damage distribution, attached-identity restrictions, obligation targeting, and cards present in the original release.

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
