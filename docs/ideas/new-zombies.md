# New Zombie Types

**Status:** Idea

## Summary

Add stronger zombies. Start with stat-boosted variants of existing zombies, in the same way vanilla does Feral and Radiated versions, and later add entirely new enemy types like Darkness Falls does.

## Goals

- Keep late game threatening once players have strong gear.
- More variety in hordes and POIs.
- Bosses and elites that are worth fighting, and can drop [Named Weapons](named-weapons.md).

## Inspiration

- Vanilla variants: normal → Feral → Radiated (and Charged / Infernal in newer versions).
- **Darkness Falls**: new enemy types and harder tiers.

## Phase 1: stat variants (XML only)

Make new tiers by building on existing zombies:

| Variant idea | Changes |
| --- | --- |
| **Mutated / Tier+1** | Higher HP and damage, tinted look, better loot |
| **Elite** | Tougher, uses a special attack or buff (bleeding, infection boost) |
| **Boss** | Lots of HP, takes less damage, guaranteed good loot, rare spawn |

Ability ideas, using buffs:

- Regenerates health unless set on fire
- Explodes on death
- Shrugs off headshots or stuns
- Faster sprint at night
- Gives buffs to nearby zombies

## Phase 2: new enemy types

New models, animations and behaviours. This needs Unity asset bundles, and maybe C# for new AI. Ideas to brainstorm:

- Ranged or spitting enemies
- Fast, small enemies that come in swarms
- Huge tank zombies
- Enemies that dig through or climb terrain

## Game systems involved

- `entityclasses.xml`: new entity classes using `extends` from existing zombies, overriding HP, speed, damage, size, tint and loot.
- `entitygroups.xml`: where and how often new zombies spawn (biomes, hordes, POI sleepers).
- `gamestages.xml`: which game stage the new types start showing up in blood moon and wandering hordes.
- `buffs.xml`: special abilities.
- `items.xml`: zombie hand or attack items for different damage and effects.
- `loot.xml`: loot from new zombies.
- `Localization.txt`: names.
- **Phase 2:** Unity assets, animation controllers, maybe C# for AI tasks.

## Plan

1. **Phase 1a:** one boosted variant of one zombie, spawned with the debug menu to test.
2. **Phase 1b:** add it to spawn groups and game stages and check difficulty in normal play.
3. **Phase 1c:** a full tier of variants across the common zombie types.
4. **Phase 1d:** boss variants for [Boss POIs](boss-pois.md).
5. **Phase 2:** prototype the first new enemy type.

## Open questions

- How should variants look different (tint, size, particles) so players can tell them apart?
- Should new tiers replace vanilla spawns at high game stages, or be added on top?
- How hard should it get, and should there be a config option for difficulty?
