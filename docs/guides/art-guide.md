# Art Guide: Icons and Crop Models

Rules for the inventory icons and 3D models we make, so new crops (wheat next) match the carrot. These come from what worked in game and from feedback on the carrot.

Reference implementations for models: [build_carrot.py](../../art/farming/carrot/build_carrot.py) and [build_wheat.py](../../art/farming/wheat/build_wheat.py) (Blender), and [FarmingBundleBuilder.cs](../../unity/BinaryNestModAssets/Assets/Editor/FarmingBundleBuilder.cs) (Unity). Icons are made with ChatGPT (section 1).

---

## 1. Icons

Icons are shown small: inventory slots, the creative menu, crafting skill rows and recipe lists. **The test for every icon is whether a player can tell what it is at a glance, at slot size, next to the vanilla icons.**

### Format

| Rule | Value |
| --- | --- |
| Size | **160 × 160** PNG, RGBA, **transparent background** |
| File name | Exactly the item or block name, e.g. `foodCropCarrot.png`, `plantedCarrot1.png` |
| Location | `Mods/BinaryNest_Farming/UIAtlases/ItemIconAtlas/` |
| XML | No `CustomIcon` on the item itself. Remove any placeholder `CustomIcon` / `CustomIconTint` lines once the PNG exists. If the item `Extends` a vanilla item that sets `CustomIcon` (e.g. wheat extends cotton), add `param1="CustomIcon"` to the `Extends` property so the icon isn't inherited. |
| Growing and grown blocks | Point at the seed icon with `CustomIcon` (e.g. `plantedCarrot1`), the same way vanilla does |

### Made with ChatGPT

**Inventory and menu icons are made with ChatGPT image generation, not rendered in Blender.** We tried rendered icons (including photo-realistic Cycles renders), and they never looked as natural as the vanilla icons, especially seed heaps. ChatGPT's images matched the game's realistic icon style far better.

Workflow:

1. **Generate** a square, photo-realistic image of the item in ChatGPT, using the composition rules below. Ask for a **transparent background** (or a plain white one to cut out).
2. **Make it a game icon:** crop so the subject fills the square, remove any background, and resize to **160 × 160** RGBA PNG.
3. **Name and place it** exactly as the Format table says, then remove any placeholder `CustomIcon` lines from the XML.
4. **Check it at slot size** (about 56 px) next to the vanilla icons in game, or with a scaled-down copy. If you can't tell what it is at that size, regenerate with a simpler composition.
5. **Licence:** OpenAI's terms currently give you the rights to images you generate, but check the current terms before a release. Don't use stock photos or images from other sites.

Example prompt (Wheat Seeds):

> Photo-realistic game inventory icon, square: a small heap of reddish-brown wheat grains with a golden ear of wheat lying in front, soft even studio lighting, sharp detail, transparent background, no text, no shadow on the background.

### Composition

These apply to whatever prompt you write.

1. **One clear subject that fills the square,** with only a small margin.
2. **Produce: a single item on a diagonal,** like the vanilla corn icon: one end at the bottom left, the top at the upper right. Show **one** item, not a group, and make it big. Keep leafy tops short so the produce itself dominates.
3. **Seeds: a heap of seeds plus the crop,** like the vanilla seed icons:
   - The seeds are the main shape and fill most of the frame.
   - Seeds use a **colour and shape specific to the crop**, so they don't look like other seeds.
   - **The seeds and the crop must contrast in colour,** or they blur into one blob at slot size (e.g. reddish-brown wheat grains with a golden ear).
   - Show the crop side-on, not pointing at the viewer, and clearly visible, not tucked in a corner.
4. **Realistic, evenly lit, no background, no text, no drop shadow,** to match the vanilla icons on the game's dark grey UI.

### Telling seeds apart

Check new seed colours against vanilla and our existing seeds:

| Seeds | Colour / shape |
| --- | --- |
| Blueberry (vanilla) | Mid brown, small |
| Goldenrod (vanilla) | Black, tiny |
| Cotton (vanilla) | White fluff with dark seeds |
| Coffee (vanilla) | Dark brown beans |
| Corn (vanilla) | Bright yellow kernels, large |
| **Carrot (ours)** | Small seeds with a carrot |
| **Wheat (ours)** | **Reddish-brown grains with a golden ear** |

---

## 2. Crop models

### Scale and layout

| Rule | Value |
| --- | --- |
| Units | 1 Blender unit = 1 metre = 1 game block |
| Origin | Where the plant meets the soil (centre of the block's bottom face). The Unity builder moves the mesh down 0.5 m to match the game's block origin. |
| Footprint | Stay inside the 1 × 1 m block. The grown carrot is about 0.8 × 0.9 m wide. |
| Stages | Three: `<Crop>Seedling`, `<Crop>Growth`, `<Crop>Harvest`. |
| Wild model | If the wild plant is hard to spot in the landscape, give the wild block (`...3Harvest`) its own bigger `<Crop>Wild` model with something eye-catching, like the wild carrot's white flower heads. The player block (`...3HarvestPlayer`) then sets its own `Model` back to `<Crop>Harvest`. |
| Determinism | Fixed random seed per stage, so rebuilding gives the same plant |

### Look

- **Leaves are cut-out cards, like vanilla.** The vanilla potato and blueberry leaves are flat cards with a leaf texture whose transparent areas cut out the leaf's outline. That's what makes them look thin and detailed. Modelling every leaflet as solid geometry looked chunky and blocky next to them. The carrot uses one flat, slightly cupped card per frond with a feathery frond texture (`CarrotFrond.png`, RGBA). Mark the material as `cutout` in the builder's `MaterialDefs`. The shader then alpha-tests it and draws both sides, and the texture import keeps leaf coverage in distant mipmaps.
- **Wheat is cards throughout:** thin crossed cards for each stem (a real wheat stem is only ~3-4 mm across; solid tubes looked far too thick), crossed cards for each ear with the spikelets and bristles in the texture, and single cards for the leaves. Everything shares one RGBA atlas (`WheatPlant.png`) with green and gold versions. Draw ear details in metres so the card's aspect doesn't stretch them.
- **Solid parts** (carrot stalks and roots) are normal geometry. Give visible solid parts a texture with some real detail (the carrot root has ring lines, darker marks and a crown), not a flat colour. Model any thin solid parts on both sides, because non-cut-out materials hide back faces.
- **Muted colours:** the game's lighting makes the Unity Standard shader look brighter and more saturated than Blender. Choose darker, less saturated colours than looks right in Blender. Carrot leaf greens are around sRGB `(0.12–0.19, 0.26–0.32, 0.07–0.10)`.
- **Variation:** generated textures with several colour variants (the carrot frond texture has two greens), picked per frond. Avoid one flat colour.
- **Don't overcrowd or regularise:** too many leaves fanned evenly around the centre, all facing up, looks computer-made. Use fewer, narrower leaves, irregular spacing, a random roll per leaf, and mirror some textures. Leave small gaps in the texture (a few missing leaflets) and vary angles.
- **Colours are sRGB values** (what Unity uses). In Blender, convert them to linear for the material (`srgb_to_linear`) so the previews match the game.

### Triangle budget and LODs

Every stage has **3 LODs** (`<Stage>_LOD0`, `_LOD1`, `_LOD2` in one FBX). Use the same random seed for each so the silhouette doesn't jump. Aim for roughly 55% of LOD0's triangles at LOD1 and 15–20% at LOD2.

Budget for the grown stage's LOD0 against vanilla crops:

| Crop | Grown LOD0 triangles |
| --- | --- |
| Potato (vanilla) | 396 (no LODs) |
| Blueberry (vanilla) | 2,000 |
| **Carrot (ours)** | **710** (LOD1 374, LOD2 186), leaf cards. Wild: 1,018 |
| **Wheat (ours)** | **1,056** (LOD1 704, LOD2 264), all cards |
| Cotton (vanilla) | 5,602 |
| Pumpkin (vanilla) | 12,538 |
| Yucca / Hops (vanilla) | 14,090 / 15,188 |

Stay at or under cotton for a low, leafy crop. Wheat is tall and dense, so expect it to sit between cotton and yucca. Lean on LODs rather than cutting LOD0 detail.

---

## 3. Unity and in-game rules (handled by the builder)

These are already automated in `FarmingBundleBuilder.cs`. A new crop only needs adding to its `Models` list, a new `MaterialDefs["<Crop>"]` entry and a `SwayDefs["<Crop>"]` entry.

- **Prefab root tag `T_Block`**, at custom tag **position 4** in the project's tag list. Without it the plant can't be aimed at or harvested. The builder checks this against the game's own plants on every build.
- **Root object** on layer 16, with a `SphereCollider` around the base of the plant.
- **`LODGroup` on the prefab root.** That's where the game reads it.
- **Wind sway:** every crop material uses our shader `BinaryNest/CropWind` ([CropWind.shader](../../unity/BinaryNestModAssets/Assets/Farming/Shaders/CropWind.shader)). It's Standard lighting plus a vertex sway driven by the game's global `_Wind` value (wind speed with gusts, and a wind clock, set every frame by the weather), so our crops move with the same weather as vanilla plants. Roots stay still and tips move most. Tune per crop in the builder's `SwayDefs` (sway height, distance, leaf flutter). The build log's `Shader check` line confirms every prefab uses it.
- **Cut-out leaf cards:** materials marked `cutout` get `_Cutoff` 0.5, `_Cull` Off and the alpha-test queue. Their textures keep alpha with coverage-preserving mipmaps.
- Textured materials use a white colour so the texture shows.
- All prefabs go into `Resources/BinaryNestFarming.unity3d`.

## 4. XML and naming rules

| What | Rule | Carrot example |
| --- | --- | --- |
| Produce name | Just the crop | Carrot |
| Seed name | `<Crop> Seeds` | Carrot Seeds |
| Grown plant label (`...3HarvestDesc`) | Just the crop, like vanilla "Chrysanthemum" | Carrot |
| Localization file | Must be `Config/Localization.csv`. The game ignores `.txt`. | |
| Wild block (`...3Harvest`) | Set `CreativeMode` to `None`. It's never inherited, and the default shows it in the creative menu. | `plantedCarrot3Harvest` |
| Items that `Extends` a vanilla item | `Extends` copies properties but **not** `effect_group`s. Repeat food, water, health and buff effects in our own item, or they'll be 0. | `foodCropCarrot` repeats the potato's `$foodAmountAdd` 2 |

---

## 5. Pipeline per crop

1. Copy `art/farming/carrot/build_carrot.py` to `art/farming/<crop>/build_<crop>.py` and change the geometry and colours.
2. Run it: `blender --background --factory-startup --python art/farming/<crop>/build_<crop>.py`. It writes the FBX files and texture into the Unity project, and previews to `art/farming/<crop>/previews/`.
3. Review the previews.
4. Make the icons with ChatGPT (section 1) and add them to `UIAtlases/ItemIconAtlas/`.
5. Add the crop's models and materials to `FarmingBundleBuilder.cs`, then run the bundle build. Check the log for `Tag check passed` and `3 LODs`.
6. Point `blocks.xml` at `#@modfolder:Resources/BinaryNestFarming.unity3d?<Stage>` and remove placeholder lines.
7. Test in game: aim, harvest, names, icons, LOD fade at distance.
