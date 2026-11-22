# Adapting Farming (BinaryNest_Farming)

Adds new crops to 7 Days to Die. See the [roadmap & spec](../../docs/roadmap/adapting-farming.md).

**Version:** 0.1.0 (in progress)
**Built against:** the vanilla config in the current Steam build of 7 Days to Die (checked 2026-11-22)

## What's in v0.1

| Item | Internal name | Notes |
| --- | --- | --- |
| Carrot | `foodCropCarrot` | Edible, same as Potato |
| Wheat | `resourceCropWheat` | Resource, not edible |
| Carrot Seeds | `plantedCarrot1` | 5 Carrots, unlocks with Yucca seeds (seed skill level 8) |
| Wheat Seeds | `plantedWheat1` | 5 Wheat, unlocks with Corn seeds (seed skill level 18) |

Growth: `planted<Crop>1` → `planted<Crop>2` → `planted<Crop>3HarvestPlayer`. Wild plants are `planted<Crop>3Harvest`.

Display names come from `Config/Localization.csv`. The game only loads a mod's localization from a file with exactly that name.

## Status of art

| What | Status |
| --- | --- |
| Carrot models (3 stages) | ✅ Custom models in `Resources/BinaryNestFarming.unity3d` |
| Carrot and Carrot Seeds icons | ✅ `UIAtlases/ItemIconAtlas/foodCropCarrot.png`, `plantedCarrot1.png` |
| Wheat models (3 stages) | ⏳ PLACEHOLDER: vanilla hops models |
| Wheat and Wheat Seeds icons | ⏳ PLACEHOLDER: tinted vanilla icons (`CustomIcon` / `CustomIconTint`) |

Every placeholder line in the XML is marked with a `PLACEHOLDER` comment.

## Rebuilding the art

1. **Models, texture and icons:** `blender --background --factory-startup --python art/farming/carrot/build_carrot.py` (from the repo root). This writes the FBX models and leaf texture into the Unity project, the icons into `UIAtlases/ItemIconAtlas/`, and preview renders to `art/farming/carrot/previews/`.
2. **Asset bundle:** run Unity 2022.3.62f2 on `unity/BinaryNestModAssets` with `-batchmode -quit -executeMethod BinaryNest.Editor.FarmingBundleBuilder.Build`, or use the **BinaryNest > Build Farming Bundle** menu in the editor. This writes `Resources/BinaryNestFarming.unity3d` into this mod and checks the prefabs' `T_Block` tag against the game's own plants.

Because the mod ships an asset bundle, multiplayer clients need the mod installed too, not just the server.

## Testing

1. Copy this folder into the game's `Mods` folder.
2. Start a new game and check the `F1` console for XML errors.
3. Use the creative menu (`U`, needs debug or creative mode) to spawn the items, or `giveself plantedCarrot1` in the console.
4. Work through the acceptance checklist in the [spec](../../docs/roadmap/adapting-farming.md#acceptance-checklist).
