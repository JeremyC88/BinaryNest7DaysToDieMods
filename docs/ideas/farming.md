# Adapting Farming

**Status:** Idea

**Roadmap:** [Adapting Farming roadmap & spec](../roadmap/adapting-farming.md)

## Summary

Make farming bigger, in the style of Darkness Falls: add new crops that grow in farm plots, add fruit trees, and possibly rework how farming works.

## Goals

- More crop variety, so food and cooking have more depth.
- Fruit trees as a long-term investment: slow to grow, but they keep producing.
- New ingredients that feed into new or existing recipes.
- Possibly make farming more involved (water, fertiliser, seasons) without making it tedious.

## Inspiration

- **Darkness Falls**: expanded crops and farming.
- Vanilla crops: corn, potato, blueberry, mushroom, pumpkin, cotton, coffee, yucca, aloe, goldenrod, chrysanthemum, hops, super corn.

## Content ideas

### Farm plot crops

| Crop | Used for (ideas) |
| --- | --- |
| Carrot | Stews, raw snack, possibly an eyesight/perception buff |
| Wheat | Flour, then bread, pastries and beer |
| *More to add* | Tomato, onion, cabbage, sugar cane, rice, grapes? |

### Trees

| Tree | Produces | Notes |
| --- | --- | --- |
| Apple Tree | Apples | Pies, cider, juice |
| Coconut Tree | Coconuts | Coconut water (hydration), coconut milk |
| Cocoa Tree | Cocoa beans | Chocolate, hot chocolate |

Should trees be biome-locked (coconut in desert or tropical areas, apple in forest)? Should they drop seeds or saplings from harvested fruit?

## Game systems involved

- `blocks.xml`: seed, growing and harvestable plant blocks, using the `PlantGrowing` class (growth stages, growth rate, what the plant becomes next).
- `items.xml`: seeds, produce, and cooked foods.
- `recipes.xml`: seed crafting, cooking recipes, and the recipes that unlock them.
- `loot.xml` / `traders.xml`: where seeds and saplings are found or bought.
- `progression.xml`: how this fits the Living Off the Land perk and crafting skill books.
- `biomes.xml`: wild versions of crops and trees spawning in the world.
- `Localization.txt`: names and descriptions.
- **Assets**: vanilla plant models can be reused or recoloured at first. Proper carrot, wheat and fruit tree models would need a Unity asset bundle.

## Plan

1. **Phase 1, one crop end to end:** add carrots using a reused model. Seed, growth stages, harvest, one recipe, and a place to get the seeds.
2. **Phase 2, more crops:** wheat, flour and bread, and the remaining farm plot crops.
3. **Phase 3, trees:** a sapling that grows into a tree and can be harvested over and over.
4. **Phase 4, custom assets:** proper models and icons.
5. **Phase 5, mechanics (optional):** watering, fertiliser, crop quality, seasons.

## Related mods

- **[Expanded Cooking](cooking.md):** a separate add-on that needs this mod. It adds recipes and cooking stations (oven, grain mill, smoker and more) that use the new crops. This mod should only add the produce plus a few basic recipes, and leave the bigger cooking content to that add-on.

## Open questions

- Should mechanics changes go in this mod, or a separate "Farming Mechanics" modlet so players can choose?
- How should new crops be balanced against vanilla food so they're worth growing?
- Can trees regrow fruit after harvest, or do they go back to an earlier growth stage?
- Should any of this need C# code (which means turning EAC off), or can it all be done in XML?
