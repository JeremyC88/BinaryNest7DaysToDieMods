# Named Weapons

**Status:** Idea

## Summary

Unique or very rare weapons, each with its own name and special abilities. They're based on existing weapon types but play differently, and they drop from tough zombies or come as POI rewards.

## Goals

- Give players something exciting to chase: a "legendary" moment when one drops.
- Each weapon should feel different, not just have bigger numbers.
- Keep them rare enough to stay special, without being so rare nobody ever sees one.

## Weapon ideas

| Name | Base type | Ability ideas |
| --- | --- | --- |
| **One Man Army** | Shotgun | Bigger magazine, faster reload, a kill streak that builds a damage or speed buff |
| **The Penetrator** | Sniper Rifle | Shots go through several enemies and some blocks, extra headshot damage |
| *More to add* | Melee, bows, pistols, explosives... | |

Possible ability building blocks:

- On-kill effects (heal, stamina back, explosions, a temporary buff)
- On-hit effects (bleed, fire, shock, knockdown, slow)
- Passive effects while held (move speed, damage resistance)
- Ammo effects (penetration, ricochet, splash damage)
- A drawback on some weapons for flavour (cursed weapons?)

## Inspiration

- Legendary or unique items in looter shooters (Borderlands, Diablo)
- Rare loot in other 7 Days to Die overhauls

## Game systems involved

- `items.xml`: new items using `Extends` to inherit from the base weapon, then override stats, name and look. Probably fixed at quality 6, or use a custom tier.
- `item_modifiers.xml`: built-in mods that can't be removed, for the special abilities.
- `buffs.xml`: triggered effects (on kill, on hit, while held).
- `loot.xml`: very low drop chances in boss zombie loot, final POI loot chests, and quest rewards.
- `entityclasses.xml`: link to boss zombies from [New Zombie Types](new-zombies.md) that can drop these.
- `quests.xml`: possibly guaranteed rewards for [Boss POIs](boss-pois.md).
- `Localization.txt`: names, descriptions and flavour text.
- **Assets (optional):** a unique tint or particle effect so the weapon can be recognised at a glance.

## Plan

1. **Phase 1:** make One Man Army as a test, with stats, one special buff, and a debug way to spawn it.
2. **Phase 2:** add The Penetrator and work out a reusable pattern (item + modifier + buff).
3. **Phase 3:** add these weapons to loot with a balanced drop rate.
4. **Phase 4:** build out the list to roughly one named weapon per weapon type.
5. **Phase 5:** visual identity (colour, effects, custom icon).

## Open questions

- Can players repair, scrap or add mods to these weapons?
- Should the stats be fixed, or vary a little between drops?
- One of each per world, or can players find duplicates?
- Should they scale with game stage, or be strong from the start but hard to get?
