# Art Guide: Icons and Crop Models

Rules for the inventory icons and 3D models we make, so new crops (wheat next) match the carrot. These come from what worked in game and from feedback on the carrot.

Reference implementation: [build_carrot.py](../../art/farming/carrot/build_carrot.py) (Blender) and [FarmingBundleBuilder.cs](../../unity/BinaryNestModAssets/Assets/Editor/FarmingBundleBuilder.cs) (Unity).

---

## 1. Icons

Icons are shown small: inventory slots, the creative menu, crafting skill rows and recipe lists. **The test for every icon is whether a player can tell what it is at a glance, at slot size, next to the vanilla icons.**

### Format

| Rule | Value |
| --- | --- |
| Size | **160 × 160** PNG, RGBA, **transparent background** |
| File name | Exactly the item or block name, e.g. `foodCropCarrot.png`, `plantedCarrot1.png` |
| Location | `Mods/BinaryNest_Farming/UIAtlases/ItemIconAtlas/` |
| XML | No `CustomIcon` on the item itself. Remove any placeholder `CustomIcon` / `CustomIconTint` lines once the PNG exists. |
| Growing and grown blocks | Point at the seed icon with `CustomIcon` (e.g. `plantedCarrot1`), the same way vanilla does |

### Composition

1. **One clear subject that fills the square.** Frame to the model's actual vertices, not its bounding box, with about 6% margin (`ortho_scale = extent × 1.06`). A rotated bounding box is far bigger than the object and leaves the subject tiny.
2. **Produce: a single item on a diagonal,** like the vanilla corn icon: tip or base at the bottom left, top at the upper right. Show **one** item, not a group, and make it big. Keep leafy tops short so the produce itself dominates.
3. **Seeds: a heap of seeds with the crop in front,** like the vanilla seed icons (e.g. blueberry seeds with blueberries):
   - The heap is the main shape and fills most of the frame.
   - Seeds are small and in a **colour and shape specific to the crop**, so they don't look like other seeds.
   - One small piece of the crop lies **side-on in front** so its shape reads clearly. Don't point it at the camera, or it turns into a blob. For the carrot: green top on the left, **point on the right**.
   - Keep the crop's leaves short so they don't spread across the frame.
4. **Camera:** orthographic. Produce is viewed from nearly straight on (slightly above). Seed heaps are viewed from about 30–35° above, so the heap has volume.

### Telling seeds apart

Check new seed colours against vanilla and our existing seeds:

| Seeds | Colour / shape |
| --- | --- |
| Blueberry (vanilla) | Mid brown, small |
| Goldenrod (vanilla) | Black, tiny |
| Cotton (vanilla) | White fluff with dark seeds |
| Coffee (vanilla) | Dark brown beans |
| **Carrot (ours)** | **Pale tan, round** |
| Wheat (planned) | Suggest **golden, elongated grains**, clearly different from carrot's round tan seeds |

### Lighting and colour

- Two sun lights: **key** (energy 4.5) from the top left, **fill** (energy 1.8) from the right, with soft angle (10°). World strength 1.2.
- View transform **Standard** (not AgX) for icons, so colours stay punchy at small size.
- Icons should look brighter and cleaner than the in-world previews. They sit on dark grey UI backgrounds.

### Checking

The build script also renders a **56 × 56** copy to `previews/icon_<name>_small.png`. Look at that before committing. If you can't tell what it is at that size, change the design rather than the lighting.

---

## 2. Crop models

### Scale and layout

| Rule | Value |
| --- | --- |
| Units | 1 Blender unit = 1 metre = 1 game block |
| Origin | Where the plant meets the soil (centre of the block's bottom face). The Unity builder moves the mesh down 0.5 m to match the game's block origin. |
| Footprint | Stay inside the 1 × 1 m block. The grown carrot is about 0.8 × 0.9 m wide. |
| Stages | Three: `<Crop>Seedling`, `<Crop>Growth`, `<Crop>Harvest`. The wild block uses the Harvest model. |
| Determinism | Fixed random seed per stage, so rebuilding gives the same plant |

### Look

- **Stylised but defined:** smooth-shaded leaves with some shape (lobes, a midrib fold), not flat single triangles.
- **Leaves are modelled on both sides.** The game's standard shader hides back faces.
- **Muted colours:** the game's lighting makes the Unity Standard shader look brighter and more saturated than Blender. Choose darker, less saturated colours than looks right in Blender. Carrot leaf greens are around sRGB `(0.12–0.19, 0.26–0.32, 0.07–0.10)`.
- **Variation:** a small generated texture with several colour variants (the carrot uses four greens), picked per frond, plus subtle veins and lighter tips. Avoid one flat colour.
- **Colours are sRGB values** (what Unity uses). In Blender, convert them to linear for the material (`srgb_to_linear`) so the previews match the game.

### Triangle budget and LODs

Every stage has **3 LODs** (`<Stage>_LOD0`, `_LOD1`, `_LOD2` in one FBX). Use the same random seed for each so the silhouette doesn't jump. Aim for roughly 55% of LOD0's triangles at LOD1 and 15–20% at LOD2.

Budget for the grown stage's LOD0 against vanilla crops:

| Crop | Grown LOD0 triangles |
| --- | --- |
| Potato (vanilla) | 396 (no LODs) |
| Blueberry (vanilla) | 2,000 |
| **Carrot (ours)** | **4,714** (LOD1 2,654, LOD2 826) |
| Cotton (vanilla) | 5,602 |
| Pumpkin (vanilla) | 12,538 |
| Yucca / Hops (vanilla) | 14,090 / 15,188 |

Stay at or under cotton for a low, leafy crop. Wheat is tall and dense, so expect it to sit between cotton and yucca. Lean on LODs rather than cutting LOD0 detail.

---

## 3. Unity and in-game rules (handled by the builder)

These are already automated in `FarmingBundleBuilder.cs`. New crops only need adding to its `Models` and `MaterialDefs` lists.

- **Prefab root tag `T_Block`**, at custom tag **position 4** in the project's tag list. Without it the plant can't be aimed at or harvested. The builder checks this against the game's own plants on every build.
- **Root object** on layer 16, with a `SphereCollider` around the base of the plant.
- **`LODGroup` on the prefab root.** That's where the game reads it.
- Standard shader. Textured materials use a white colour so the texture shows.
- All prefabs go into `Resources/BinaryNestFarming.unity3d`.

## 4. XML and naming rules

| What | Rule | Carrot example |
| --- | --- | --- |
| Produce name | Just the crop | Carrot |
| Seed name | `<Crop> Seeds` | Carrot Seeds |
| Grown plant label (`...3HarvestDesc`) | Just the crop, like vanilla "Chrysanthemum" | Carrot |
| Localization file | Must be `Config/Localization.csv`. The game ignores `.txt`. | |
| Wild block (`...3Harvest`) | Set `CreativeMode` to `None`. It's never inherited, and the default shows it in the creative menu. | `plantedCarrot3Harvest` |

---

## 5. Pipeline per crop

1. Copy `art/farming/carrot/build_carrot.py` to `art/farming/<crop>/build_<crop>.py` and change the geometry, colours and icon composition.
2. Run it: `blender --background --factory-startup --python art/farming/<crop>/build_<crop>.py`. It writes the FBX files and texture into the Unity project, the icons into the mod, and previews to `art/farming/<crop>/previews/`.
3. Review the previews, including the `_small` icons.
4. Add the crop's models and materials to `FarmingBundleBuilder.cs`, then run the bundle build. Check the log for `Tag check passed` and `3 LODs`.
5. Point `blocks.xml` at `#@modfolder:Resources/BinaryNestFarming.unity3d?<Stage>` and remove placeholder lines.
6. Test in game: aim, harvest, names, icons, LOD fade at distance.
