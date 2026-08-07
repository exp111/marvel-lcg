# Marvel LCG Digital — Community Build

This community-maintained build is based on [Marvel LCG Digital](https://irefrixs.itch.io/marvel-lcg), originally developed by the Irefrixs Team. It adds campaign support, community content, gameplay corrections, and interface improvements while keeping the game free to play.

The upstream developers have given permission for modified builds to be published while they finalize a permissive software license. See [ATTRIBUTION.md](ATTRIBUTION.md) for project and intellectual-property notices.

## Latest release: v1.0.0.5

[Download Community Build v1.0.0.5 for Windows](https://github.com/sdolle1775/marvel-lcg/releases/tag/v1.0.0.5)

This release includes all v1.0.0.4 hotfixes for Wonder Man, Hercules, Synthezoid Smackdown, and the Agents of S.H.I.E.L.D. campaign, plus these additional corrections:

- Ancient Rivalry can be played while Hercules and Thor are both in play.
- Teamwork and similar matching-power effects correctly use an ally's ATK when thwarting an assault scheme.
- Hercules and Wonder Man reprints of existing cards use their original implementations.
- The main menu identifies the game as the Community Build and displays the current application version.

Campaign setup choices are saved in `campaign_settings.json`. When installing a new release, extract it into a new folder and copy this file from the previous installation to preserve those choices. Also copy any saves, replays, or custom decks you want to retain. Keep `marvel-lcg.exe` beside its `_internal` folder, and do not copy the old executable or old `public`, `data`, or cache folders into the new installation.

See the [complete patch notes](PATCH_NOTES.md) and [installation guide](docs/install_guide.md) for details.

## Antivirus scan and Windows packaging

v1.0.0.5 uses a Python 3.12 PyInstaller one-folder package with UPX disabled. This avoids the previous one-file executable's self-extraction into a temporary directory, which can contribute to heuristic antivirus detections.

The [VirusTotal results for the exact v1.0.0.5 executable](https://www.virustotal.com/gui/file/db4cd4e71296a4de9f90bf2da712c0e767d2ff7c0f865d8258763d398cb1709e/detection) are comparable to those of the original development team's executable; this is not a promise of zero detections. The build is currently unsigned, so Microsoft SmartScreen or individual antivirus products may still display a warning.

- Executable SHA-256: `db4cd4e71296a4de9f90bf2da712c0e767d2ff7c0f865d8258763d398cb1709e`
- Release ZIP SHA-256: `af6944dd33eb9e50b75042c85dd35b6f7d4f5b8f53391c31d43655a2743e7d47`

## Community build highlights

- Campaign setup choices persist locally across launches for every campaign.
- Agents of S.H.I.E.L.D. evidence rewards, Setup abilities, Evidence Seed handling, and persistent Executive Board attachments follow the campaign rules.
- Wonder Man and Hercules include their complete registered nemesis content, with corrected obligation, attack, activation, and fallback-search behavior.
- Complete campaign flows for **Mutant Genesis**, **NeXt Evolution**, **Age of Apocalypse**, **Agents of S.H.I.E.L.D.**, **Galaxy's Most Wanted**, and **The Mad Titan's Shadow**.
- New **Synthezoid Smackdown** cooperative scenarios and encounter sets.
- New playable **Wonder Man** and **Hercules** hero expansions with starter decks.
- An adjustable card-interaction speed setting changes presentation timing without affecting gameplay resolution.
- Improved MarvelCDB deck imports, hotseat prompt ownership, card-image loading, browser cache handling, and card interaction reliability.
- Rules corrections cover fixed-total threat and damage distribution, attached-identity restrictions, and cards present in the original release.

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
