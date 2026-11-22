# Adapting Farming: Roadmap & Spec

Versions of [Adapting Farming](../ideas/farming.md) and what each one includes. The next version is specified in detail. Later versions are rough until they become the next one.

| Version | Theme | Status |
| --- | --- | --- |
| [v0.1](#v01-carrots-and-wheat) | Carrots and Wheat | Planned |
| [v0.2+](#later-versions-tentative) | More crops, trees, mechanics | Tentative |

---

## v0.1: Carrots and Wheat

**Goal:** add two new crops that work just like vanilla crops. Players can find them in the wild, find or buy seeds, plant them, watch them grow, harvest them, and craft more seeds.

### 1. Inventory items

| Item | Description | Icon |
| --- | --- | --- |
| Carrot Seed | Plantable seed that places the first growth stage | New |
| Wheat Seed | Plantable seed that places the first growth stage | New |
| Carrot | Food item with the same food and water values as the vanilla Potato | New |
| Wheat | Crafting resource, **not edible raw** | New |

- Carrot should `Extends` the vanilla potato item, so it inherits its stats and stays in line if the game rebalances it.
- Wheat is a plain resource item with no eat action. In v0.1 its only use is crafting seeds. Flour, bread and the rest come with [Expanded Cooking](../ideas/cooking.md).
- Icons go in `UIAtlases/ItemIconAtlas/`, with each file named exactly like the item or block it belongs to.

### 2. Recipes

| Output | Ingredients | Notes |
| --- | --- | --- |
| 1× Carrot Seed | 5× Carrot | Unlocked at the same progression level as Yucca seeds |
| 1× Wheat Seed | 5× Wheat | Unlocked at the same progression level as Corn seeds |

- Seed crafting is gated by progression, the same way vanilla seeds are. In v0.1 that's the vanilla farming progression (Living Off the Land). A later version will move the unlocks to farming skill books.

### 3. Planting and growth

- Seeds can be planted anywhere vanilla seeds can: farm plot blocks and normal soil.
- Each crop has three growth stages, each with a **new render**:

| Stage | Carrot | Wheat |
| --- | --- | --- |
| 1. Seedling | New render | New render |
| 2. Part grown | New render | New render |
| 3. Grown (harvestable) | New render | New render |

- Growth time, harvest yield, and the bonus from the Living Off the Land perk all match the vanilla potato.
- Harvesting a grown crop drops Carrots or Wheat, the same way the potato drops potatoes.
- Follow the vanilla seed → growing → harvest block pattern, using the potato blocks in `blocks.xml` as the template.

### 4. Wild foraging

| Crop | Biome | Works like | Render |
| --- | --- | --- | --- |
| Carrot | Forest | Wild Goldenrod | Uses the grown (stage 3) render |
| Wheat | Desert | Wild Yucca | Uses the grown (stage 3) render |

- Wild plants are separate blocks from the player-planted ones, the same way vanilla handles them. Harvesting one drops the crop and doesn't regrow.
- Spawn rates are added in `biomes.xml` and start at roughly the same rate as Goldenrod or Yucca.

### 5. Traders and loot

- **Trader Rekt** can sell Carrot Seeds and Wheat Seeds (`traders.xml`). They're part of his random stock, so they won't be there every restock, the same as other trader items.
- Seeds show up in the same loot as vanilla seeds, such as kitchen cupboards. The simplest way is to add them to the vanilla seed loot group(s) in `loot.xml`, so they appear everywhere vanilla seeds already do.

### 6. Localization

- Names and descriptions for all four items and every growth-stage block, in `Config/Localization.txt`.

### Files touched

| File | Changes |
| --- | --- |
| `ModInfo.xml` | Name, version `0.1.0`, description, author |
| `Config/items.xml` | Carrot, Wheat |
| `Config/blocks.xml` | Seed, growing and harvest blocks for each crop, plus wild variants |
| `Config/recipes.xml` | Two seed recipes |
| `Config/progression.xml` | Seed recipe unlocks (Carrot at the Yucca level, Wheat at the Corn level) |
| `Config/biomes.xml` | Wild carrot (forest) and wild wheat (desert) |
| `Config/loot.xml` | Seeds added to seed loot groups |
| `Config/traders.xml` | Seeds added to Trader Rekt |
| `Config/Localization.txt` | All new names and descriptions |
| `UIAtlases/ItemIconAtlas/` | Icons for the four items |
| `Resources/` | Unity asset bundle with the six growth-stage models |

> **Note on renders:** the new models are the biggest piece of work in v0.1, and they're the only part that isn't XML. They need a Unity asset bundle, which also means clients have to install the mod in multiplayer. To get started, the vanilla potato and corn models can stand in as placeholders so the XML can be built and tested before the real models are ready.

### Out of scope for v0.1

- Any recipe that uses Carrot or Wheat apart from seeds. That belongs in [Expanded Cooking](../ideas/cooking.md).
- Trees, other crops, or changes to farming mechanics.

### Acceptance checklist

- [ ] Game loads with no XML errors in the console or log.
- [ ] All four items show their correct icon, name and description.
- [ ] Carrot gives the same food and water as a Potato when eaten.
- [ ] Wheat can't be eaten.
- [ ] Both seeds can be planted in a farm plot and in normal soil.
- [ ] Both crops go through all three growth stages, each showing the right render.
- [ ] Harvesting a grown crop gives Carrots or Wheat, with the same yield as a potato (Living Off the Land bonus included).
- [ ] 5 Carrots craft 1 Carrot Seed, and 5 Wheat craft 1 Wheat Seed.
- [ ] Carrot Seed can't be crafted until the Yucca seed level is unlocked, then becomes available.
- [ ] Wheat Seed can't be crafted until the Corn seed level is unlocked, then becomes available.
- [ ] Wild carrots spawn in a new forest world, and wild wheat spawns in the desert.
- [ ] Wild plants use the grown render and drop the crop when harvested.
- [ ] Trader Rekt sometimes has the seeds in stock, but not every restock (check over several restocks).
- [ ] Seeds turn up in kitchen cupboards and other seed loot.
- [ ] Multiplayer: works on a dedicated server with the mod on both server and client.

### Decisions

- **Seed crafting is gated:** Carrot Seed unlocks at the same level as Yucca seeds, and Wheat Seed later, at the same level as Corn seeds. Later versions will use farming skill books instead.
- **Raw wheat isn't edible:** it's only a crafting resource.
- **Trader Rekt stock is random:** the seeds are in his random selection, not guaranteed.

### Open questions for v0.1

- None right now.

---

## Later versions (tentative)

Rough ideas based on the [plan in the idea page](../ideas/farming.md#plan). They'll be firmed up once v0.1 is done.

- **v0.2:** more farm plot crops (tomato, onion, cabbage, sugar cane...).
- **v0.3:** fruit trees: apple, coconut and cocoa, from sapling to a tree that can be harvested over and over.
- **v0.4:** balance and polish, and the hooks [Expanded Cooking](../ideas/cooking.md) needs.
- **Farming skill books (version TBD):** move seed and crop unlocks from the vanilla perk to a set of farming skill books.
- **v1.0:** first public release.
- **Later:** optional farming mechanics (watering, fertiliser, crop quality, seasons).
