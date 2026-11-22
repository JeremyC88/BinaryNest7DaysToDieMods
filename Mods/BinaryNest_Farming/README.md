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
| Carrot models (3 stages) | ✅ Custom models in `Resources/BinaryNestFarming.unity3d`, with cut-out leaf cards and 3 LODs each (grown carrot: 710 / 374 / 186 triangles). Wild carrots use a bigger `CarrotWild` model with white flower heads so they're easy to spot |
| Carrot and Carrot Seeds icons | ✅ `UIAtlases/ItemIconAtlas/foodCropCarrot.png`, `plantedCarrot1.png` (made with ChatGPT) |
| Wheat models (3 stages) | ✅ Custom models in the same bundle, built from cut-out cards with 3 LODs each (grown wheat: 1,056 / 704 / 264 triangles) |
| Wheat and Wheat Seeds icons | ✅ `resourceCropWheat.png`, `plantedWheat1.png` (made with ChatGPT) |

## Rebuilding the art

Icons and models follow the [art guide](../../docs/guides/art-guide.md).

1. **Models and textures:** from the repo root, run `blender --background --factory-startup --python art/farming/<crop>/build_<crop>.py` for each crop (`carrot`, `wheat`). Each script writes its FBX models and texture into the Unity project, and preview renders to `art/farming/<crop>/previews/`. Icons are made separately with ChatGPT (see the art guide).
2. **Asset bundle:** run Unity 2022.3.62f2 on `unity/BinaryNestModAssets` with `-batchmode -quit -executeMethod BinaryNest.Editor.FarmingBundleBuilder.Build`, or use the **BinaryNest > Build Farming Bundle** menu in the editor. This writes `Resources/BinaryNestFarming.unity3d` into this mod and checks the prefabs' `T_Block` tag against the game's own plants.

The crop models use a custom wind shader (`BinaryNest/CropWind`) so they sway with the game's weather like vanilla plants.

Because the mod ships an asset bundle, multiplayer clients need the mod installed too, not just the server.

## Testing

1. Copy this folder into the game's `Mods` folder.
2. Start a new game and check the `F1` console for XML errors.
3. Use the creative menu (`U`, needs debug or creative mode) to spawn the items, or `giveself plantedCarrot1` in the console.
4. Work through the acceptance checklist in the [spec](../../docs/roadmap/adapting-farming.md#acceptance-checklist).
