# Overhaul Mod

**Status:** Idea

**Working title:** Nest Pack

## Summary

Not fully defined yet. To start with, this is a combined pack of every BinaryNest mod so they can be tested together for compatibility. Once there are enough mods, it might become a released overhaul with its own identity.

## Goals

### Now: compatibility testbed

- Load every BinaryNest modlet at once and check that they work together.
- Catch XPath conflicts (two mods patching the same node), duplicate names, and balance problems.
- Keep a known-good set of mod versions that work together.

### Later (maybe): released overhaul

- A single install with a consistent theme and balance across all features.
- Possibly its own changes on top (progression, difficulty, UI) that don't make sense as separate modlets.

## How it could work

- **Option A, mod list:** the overhaul is just a documented list of modlets, plus a script that copies them into the game's `Mods` folder.
- **Option B, glue modlet:** a small `BinaryNest_NestPack` modlet that loads last (load order is alphabetical by folder name) and contains only the patches needed to link the mods together, such as zombie loot tables including named weapons or boss POIs using boss zombies.
- **Option C, merged mod:** combine everything into one mod for release.

The likely path is to start with A and B and only consider C when releasing.

## Compatibility checklist

- [ ] Game starts with no XML or XPath errors in the console or log (`F1` console, `output_log` file).
- [ ] No duplicate item, block, buff or entity names across the mods.
- [ ] Every new item has a localization entry and an icon.
- [ ] New loot shows up at sensible rates when everything is installed.
- [ ] RWG world generates successfully with all POIs.
- [ ] Multiplayer: a dedicated server with all mods installed works, and clients connect.
- [ ] Performance check on a blood moon with the new zombies.

## Open questions

- Final name and theme, if it gets released? ("Nest Pack" is a placeholder for now.)
- Should it also support popular third-party mods, or only BinaryNest mods?
- How will versions be tracked: one overhaul version mapped to specific modlet versions?
