# Adapting Farming (BinaryNest_Farming)

Adds new crops to 7 Days to Die. See the [roadmap & spec](../../docs/roadmap/adapting-farming.md).

**Version:** 0.1.0 (in progress)
**Built against:** the vanilla config in the current Steam build of 7 Days to Die (checked 2026-11-22)

## What's in v0.1

| Item | Internal name | Notes |
| --- | --- | --- |
| Carrot | `foodCropCarrot` | Edible, same as Potato |
| Wheat | `resourceCropWheat` | Resource, not edible |
| Carrot (Seed) | `plantedCarrot1` | 5 Carrots, unlocks with Yucca seeds (seed skill level 8) |
| Wheat (Seed) | `plantedWheat1` | 5 Wheat, unlocks with Corn seeds (seed skill level 18) |

Growth: `planted<Crop>1` → `planted<Crop>2` → `planted<Crop>3HarvestPlayer`. Wild plants are `planted<Crop>3Harvest`.

## Placeholders still to replace

| What | Currently | Replace with |
| --- | --- | --- |
| Item icons (4) | Tinted vanilla icons via `CustomIcon` / `CustomIconTint` | 160×160 PNGs in `UIAtlases/ItemIconAtlas/`, named after the item (e.g. `foodCropCarrot.png`), then delete the placeholder lines |
| Carrot models (3 stages) | Vanilla potato plant models | New renders in a Unity asset bundle in `Resources/` |
| Wheat models (3 stages) | Vanilla hops plant models | New renders in a Unity asset bundle in `Resources/` |

Every placeholder line in the XML is marked with a `PLACEHOLDER` comment.

## Testing

1. Copy this folder into the game's `Mods` folder.
2. Start a new game and check the `F1` console for XML errors.
3. Use the creative menu (`U`, needs debug or creative mode) to spawn the items, or `giveself plantedCarrot1` in the console.
4. Work through the acceptance checklist in the [spec](../../docs/roadmap/adapting-farming.md#acceptance-checklist).
