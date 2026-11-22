# New Boss POIs

**Status:** Idea

## Summary

New points of interest that go beyond vanilla Tier 5 in size and difficulty: endgame dungeons with boss fights and top-tier rewards.

## Goals

- Give fully geared players a real endgame challenge.
- Big, memorable places with a planned route, story clues, and a final boss room.
- Rewards worth the effort, such as [Named Weapons](named-weapons.md) and top-tier loot.

## Concept ideas

- **Tier 6 quests:** traders give these once all Tier 5 quests are done.
- **Possible themes:** collapsed research facility, military bunker complex, hospital at the centre of the outbreak, mega-mall, dam or power plant.
- **Structure:** several floors or zones, harder enemies the deeper you go, a boss room, a final loot vault.
- **Mechanics to explore:** locked sections that need keys found inside, traps, puzzles or power switches, and a time limit or alarm.

## Game systems involved

- **Prefab editor (in game):** build the POI. A prefab is a set of files: `.tts`, `.xml`, `.nim`, `.ins`, `.mesh`, and a preview image.
- **Prefab XML:** difficulty tier, quest tags, zoning (which biomes and town types it can appear in), and size.
- **Sleeper volumes:** use spawn groups from [New Zombie Types](new-zombies.md), including bosses.
- `rwgmixer.xml`: let random world generation place the POI.
- `quests.xml`: Tier 6 quest definitions and rewards.
- `traders.xml` / trader quest tiers: how players unlock Tier 6.
- `loot.xml`: special loot containers for the final rooms.
- `blocks.xml` (optional): custom blocks such as boss loot chests, key doors and switches.

## Plan

1. **Phase 1:** learn the prefab editor by building a small test POI. Check that it loads from the modlet's `Prefabs/` folder and appears in RWG.
2. **Phase 2:** design the first boss POI on paper (theme, layout, route, encounters).
3. **Phase 3:** build it, add sleepers and loot, and play test.
4. **Phase 4:** connect it to Tier 6 trader quests.
5. **Phase 5:** more boss POIs with different themes.

## Open questions

- Is RWG placement enough, or are these quest-only locations?
- Does Tier 6 need C# changes to the trader quest system, or can XML do it?
- How big can a POI get before it causes performance or RWG placement problems?
- Should POIs reset or respawn for replaying, the same way vanilla quests do?
