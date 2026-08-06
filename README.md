# Marvel LCG Digital — community build

This community-maintained build is based on [Marvel LCG Digital](https://irefrixs.itch.io/marvel-lcg), originally developed by the Irefrixs Team. It adds campaign support, community content, gameplay corrections, and interface improvements while keeping the game free to play.

The upstream developers have given permission for modified builds to be published while they finalize a permissive software license. See [ATTRIBUTION.md](ATTRIBUTION.md) for project and intellectual-property notices.

## What's new in community release 1.0

- Campaign setup choices now persist locally across launches in `campaign_settings.json` for every campaign.
- Agents of S.H.I.E.L.D. evidence rewards, Setup abilities, Evidence Seed handling, and persistent Executive Board attachments now follow the campaign rules.
- Complete campaign flows for **Mutant Genesis**, **NeXt Evolution**, **Age of Apocalypse**, **Agents of S.H.I.E.L.D.**, **Galaxy's Most Wanted**, and **The Mad Titan's Shadow**.
- New **Synthezoid Smackdown** cooperative scenarios and encounter sets.
- New playable **Wonder Man** and **Hercules** hero expansions with starter decks.
- An adjustable card-interaction speed setting that changes presentation timing without affecting gameplay resolution.
- Improved MarvelCDB deck imports, hotseat prompt ownership, card-image loading, browser cache handling, and card interaction reliability.
- Rules corrections for fixed-total threat and damage distribution, attached-identity restrictions, and cards present in the original release.
- Reproducible Windows packaging with checksums and an automated GitHub build workflow.

[Read the complete release 1.0 patch notes](PATCH_NOTES.md).

## Release and distribution

- [Release build and publishing guide](docs/release_guide.md)
- Standard card artwork is downloaded from the image servers configured in `launch.json` and cached locally. Downloaded card images are not included in the main release archive.
- The release build includes the small sounds, card backs, status cards, placeholders, and set textures required by the interface.

## Documentation

| Guide                                                          | Description                       |
| -------------------------------------------------------------- | --------------------------------- |
| [Install Guide](docs/install_guide.md)                         | How to install and run the game   |
| [How to Play](https://itch.io/t/3763917/how-to-play-this-game) | Game rules and controls           |
| [Card Scripting Guide](docs/card_scripting_guide.md)           | How to write card ability scripts |
| [Engine Architecture](docs/engine_architecture.md)             | Engine internals for developers   |
| [Debug Guide](docs/debug_guide.md)                             | How to debug the game             |
| [Editor Guide](docs/editor_guide.md)                           | How to use the card editor        |
| [Release Guide](docs/release_guide.md)                         | How to validate and package a release |

## Security Warning

This game runs Python card scripts, which is not safe.  
Do not install or run any third-party card scripts unless you trust them.

这个游戏会运行用 Python 编写的卡牌脚本，这不安全。  
除非你完全信任，否则不要安装或运行任何第三方的卡牌脚本。

## Snapshot

![](/docs/assets/image-1.jpg)
![](/docs/assets/image-2.jpg)
