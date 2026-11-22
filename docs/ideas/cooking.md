# Expanded Cooking

**Status:** Idea

**Requires:** [Adapting Farming](farming.md)

## Summary

An add-on to Adapting Farming that turns the new crops into food. It adds new recipes and new cooking stations, such as an oven, so farming leads into a proper cooking system instead of everything being made at the campfire.

## Goals

- Give every new crop a use, so farming feels worth doing.
- Make food progress over time: simple campfire meals early, better meals from advanced stations later.
- Make better food worth the effort, with longer-lasting or stronger buffs.
- Keep it a separate modlet, so players can use the farming mod without the cooking changes.

## Why a separate mod

- Adapting Farming stays focused on growing things, and stays smaller and easier to keep compatible.
- Players who use a different food or cooking mod can still use the farming mod.
- Cooking can be built and balanced at its own pace once the crops exist.

## Dependency on Adapting Farming

There's no strict "requires" setting in a modlet, so the dependency is handled through load order and documentation:

- **Load order:** mods load alphabetically by folder name, and cooking needs to load after farming because it uses the farming items. Naming it `BinaryNest_Farming_Cooking` makes it sort straight after `BinaryNest_Farming`. A name like `BinaryNest_Cooking` would load first and break.
- **Documentation:** the mod's README and `ModInfo.xml` description should say it needs Adapting Farming.
- **Failure mode:** if farming is missing, recipes that use its items will cause XML errors or simply not show up. This should be tested so the result is known.

## Cooking stations

| Station | Used for | Unlock idea |
| --- | --- | --- |
| **Campfire** (vanilla) | Basic meals, boiling, grilling | Start of the game |
| **Oven** | Bread, pies, pastries, roasts, baked meals | Mid game, with a cooking skill magazine or perk |
| **Grain Mill / Quern** | Wheat into flour, corn into cornmeal | Early to mid game, needed before baking |
| **Smoker** | Smoked meat and fish that keep longer, jerky | Mid game |
| **Brewing Barrel / Still** | Beer, cider, spirits, juice | Mid to late game |
| **Press / Juicer** | Fruit juice, oils, coconut milk | Mid game |
| *Possible later* | Butter churn, pressure cooker, kitchen counter set | |

Some of these might be better as **tools** inside a station than as separate blocks. Vanilla already does this with the cooking pot and grill in the campfire. For example, a baking tray could go in the oven, or a mortar and pestle could go in the campfire.

## Recipe ideas

Grouped by the farming crop they use.

| Crop | Recipes |
| --- | --- |
| **Wheat** | Flour → bread, pastry dough, pie crust, pasta. Beer. |
| **Carrot** | Carrot soup, roast vegetables, carrot cake |
| **Apple** | Apple pie, cider, apple juice, baked apples |
| **Coconut** | Coconut water (hydration), coconut milk, coconut curry |
| **Cocoa** | Chocolate bar, hot chocolate (warmth buff?), chocolate cake |
| **Vanilla crops** | Combined with new items: potato and carrot stew, corn bread, blueberry pie |

Ideas for meal tiers:

- **Tier 1, snacks** (campfire): small food and water gain, short buffs.
- **Tier 2, meals** (oven or smoker): bigger food gain, a single buff such as stamina regen, warmth or carry weight.
- **Tier 3, feasts** (oven plus several ingredients): large food gain and several long-lasting buffs. Rare ingredients from trees.

## Game systems involved

- `blocks.xml`: new workstation blocks using the `Workstation` class, with fuel, tool and output slots.
- `xui.xml` / XUi windows: the crafting window for each new station. These can usually reuse or copy the campfire or forge window layouts.
- `recipes.xml`: new recipes using `craft_area` (which station) and `craft_tool` (which tool), and changes to some vanilla food recipes.
- `items.xml`: ingredients (flour, dough), meals, drinks, and station tools.
- `buffs.xml`: food and drink buffs.
- `progression.xml`: how stations and recipes unlock (the Master Chef perk and the Home Cooking Weekly magazines in recent versions).
- `loot.xml` / `traders.xml`: finding or buying station parts, recipes and tools.
- `Localization.txt`: names and descriptions.
- **Assets:** vanilla models can stand in for stations at first (the oven could reuse a kitchen stove model). Icons for new foods would go in `UIAtlases/`.

## Plan

1. **Phase 1, recipes only:** new recipes at the vanilla campfire using farming crops. This proves the dependency and load order work.
2. **Phase 2, first station:** the grain mill and oven, so wheat → flour → bread works end to end.
3. **Phase 3, more stations:** smoker, brewing barrel and press.
4. **Phase 4, meal tiers and buffs:** balance food values and buffs across the tiers.
5. **Phase 5, polish:** custom models and icons, and unlocks through progression.

## Open questions

- Should vanilla food recipes move to the new stations (for example, bread needs an oven), or should vanilla stay as it is with only additions?
- Do stations need fuel like the campfire, or something else (electricity for a late-game oven)?
- How strong should food buffs be compared to vanilla, and should they stack?
- Should food spoil? It would make the smoker and other preserving methods more useful, but it's a big change and probably needs C# code.
- Should drinks with alcohol have downsides (blurred vision, less accuracy)?
