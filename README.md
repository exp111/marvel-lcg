# Marvel LCG Digital — Community Build

This community-maintained build is based on [Marvel LCG Digital](https://irefrixs.itch.io/marvel-lcg), originally developed by the Irefrixs Team. It adds campaign support, community content, gameplay corrections, and interface improvements while keeping the game free to play.

The upstream developers have given permission for modified builds to be published while they finalize a permissive software license. See [ATTRIBUTION.md](ATTRIBUTION.md) for project and intellectual-property notices.

## Latest testing release: v1.1.1

[Download Community Build v1.1.1 for Windows](https://github.com/sdolle1775/marvel-lcg/releases/tag/v1.1.1)

This prerelease includes the complete Trickster Takeover and Civil War content from v1.1.0 together with the latest gameplay, importing, and interface corrections:

- Loki Avatar swaps preserve remaining hit points and apply attached Focus bonuses once; Synergy environments now modify the resolving event, and the affected side-scheme icons are corrected.
- Enchantress I now places her charm counter after attacking.
- MarvelCDB imports distinguish heroes who share a name, including T'Challa and Shuri as Black Panther and Peter Parker and Miles Morales as Spider-Man.
- Blindfold and other ordered encounter-card selections preserve the displayed order when cards are returned.
- Player-assigned forced obligations resolve through the correct player, fixing the Protect Humanity ally-redirection freeze, and attack-animation cleanup no longer reapplies a completed transform.
- The card-data checksum and identity lookup path are synchronized with the final content, eliminating the reported checksum mismatch and false identity warning.

It also includes all campaigns, heroes, scenarios, modular sets, interface improvements, and accumulated corrections from the v1.0 and v1.1.0 community releases.

Campaign setup choices are saved in `campaign_settings.json`. When installing a new release, extract it into a new folder and copy this file from the previous installation to preserve those choices. Also copy any saves, replays, or custom decks you want to retain. Keep `marvel-lcg.exe` beside its `_internal` folder, and do not copy the old executable or old `public`, `data`, or cache folders into the new installation.

See the [complete patch notes](PATCH_NOTES.md) and [installation guide](docs/install_guide.md) for details.

## Antivirus scan and Windows packaging

v1.1.1 uses a Python 3.12 PyInstaller one-folder package with UPX disabled and a locally compiled PyInstaller bootloader. This avoids the previous one-file executable's self-extraction into a temporary directory and reduces generic heuristic antivirus detections.

The [VirusTotal report for the exact v1.1.1 executable](https://www.virustotal.com/gui/file/a650db6b493869fc993206b66e2161f38ea2d19210fe40324c07e16688b29c96?nocache=1) reports **1/70**, with only SecureAge's generic detection; Microsoft is undetected. A local Microsoft Defender custom scan also completed with no detections. The build remains unsigned, so Microsoft SmartScreen or individual antivirus products may still display a warning.

- v1.1.1 executable SHA-256: `a650db6b493869fc993206b66e2161f38ea2d19210fe40324c07e16688b29c96`
- v1.1.1 release ZIP SHA-256: `672985f0c691f51eb719bef58d1c3b75f652730a9d0f63803630957dd1f979dd`

## Community build highlights

- Complete standard and expert **Loki: God of Lies** content from Trickster Takeover, including the Avatar stages, Synergy environments, Shatter the Illusion, and Trickster Magic.
- Complete expert variants for the **Iron Man**, **Captain Marvel**, **Captain America**, and **Spider-Woman** Civil War scenarios.
- Complete campaign flows for **Mutant Genesis**, **NeXt Evolution**, **Age of Apocalypse**, **Agents of S.H.I.E.L.D.**, **Galaxy's Most Wanted**, and **The Mad Titan's Shadow**.
- New **Synthezoid Smackdown** cooperative scenarios and encounter sets.
- New playable **Wonder Man** and **Hercules** hero expansions with starter decks.
- Campaign setup choices persist locally across launches for every campaign.
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
