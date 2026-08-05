# Marvel LCG Digital — community build

This community-maintained build is based on [Marvel LCG Digital](https://irefrixs.itch.io/marvel-lcg), originally developed by the Irefrixs Team. It adds campaign support, community content, gameplay corrections, and interface improvements while keeping the game free to play.

The upstream developers have given permission for modified builds to be published while they finalize a permissive software license. See [ATTRIBUTION.md](ATTRIBUTION.md) for project and intellectual-property notices.

## Release information

- [Release 1.0 patch notes](PATCH_NOTES.md)
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
