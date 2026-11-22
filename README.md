# BinaryNest 7 Days to Die Mods

A collection of mods (modlets) for [7 Days to Die](https://7daystodie.com/), built by BinaryNest.

> **Status:** Early days. No mods have been released yet. Planned work is tracked in [docs/ideas](docs/ideas/README.md).

## Planned mods

| Mod | Summary | Docs |
| --- | --- | --- |
| Adapting Farming | New crops (carrots, wheat) and fruit trees (apple, coconut, cocoa), plus possible changes to how farming works | [farming.md](docs/ideas/farming.md), [roadmap](docs/roadmap/adapting-farming.md) |
| Expanded Cooking | Add-on to Adapting Farming: new recipes and cooking stations such as ovens, mills and smokers. Requires Adapting Farming | [cooking.md](docs/ideas/cooking.md) |
| Named Weapons | Rare, uniquely named weapons with special abilities, found in zombie loot or POI rewards | [named-weapons.md](docs/ideas/named-weapons.md) |
| New Zombie Types | Stronger variants of existing zombies first, then entirely new enemy types | [new-zombies.md](docs/ideas/new-zombies.md) |
| New Boss POIs | Endgame POIs bigger and harder than Tier 5 | [boss-pois.md](docs/ideas/boss-pois.md) |
| Overhaul Mod (working title: Nest Pack) | Combines all the mods to test compatibility; may become a release later | [overhaul.md](docs/ideas/overhaul.md) |

## Repository layout

```
BinaryNest7DaysToDieMods/
├── README.md          # This file
├── docs/
│   ├── guides/        # How-to guides (C# modding, art)
│   ├── ideas/         # Design notes, one file per mod idea
│   └── roadmap/       # Versioned specs: what goes in each release
├── Mods/              # One folder per modlet
└── unity/
    └── BinaryNestModAssets/  # Unity 2022.3.62f2 project for building asset bundles (models)
```

Each modlet will follow the standard 7 Days to Die layout:

```
Mods/
└── BinaryNest_ModName/
    ├── ModInfo.xml        # Name, version, author, description
    ├── Config/            # XPath patches to the game's XML (items.xml, blocks.xml, ...)
    │   └── Localization.txt
    ├── Resources/         # (optional) Unity asset bundles: models, textures, sounds
    ├── Prefabs/           # (optional) Custom POIs
    └── UIAtlases/         # (optional) Item and icon images
```

Prefixing every folder with `BinaryNest_` keeps the mods grouped together and makes load order (alphabetical by folder name) easy to predict.

## Installing a mod

1. Find your game folder (Steam: right-click 7 Days to Die → Manage → Browse local files).
2. Create a `Mods` folder there if it doesn't exist.
3. Copy the modlet folder (for example `BinaryNest_NamedWeapons`) into `Mods`.
4. Start the game. For multiplayer, the server needs the mod too. Mods that ship custom assets (`Resources/`) also have to be installed on every client.

Mods that only change XML usually run with Easy Anti-Cheat (EAC) on. Mods with custom C# code (DLLs) need EAC turned off.

## Development notes

- **XML first:** keep as much as possible to XPath patches in `Config/`. They're the easiest to keep compatible with game updates and with other mods. When code is needed, follow the [C# modding guide](docs/guides/csharp-modding.md).
- **Test in isolation, then together:** test each modlet on its own first, then with everything else through the Overhaul Mod.
- **Game version:** each modlet's `ModInfo.xml` and README will say which game version it was built and tested on.
- **Art:** icons and models follow the [art guide](docs/guides/art-guide.md).

## License

Not chosen yet.
