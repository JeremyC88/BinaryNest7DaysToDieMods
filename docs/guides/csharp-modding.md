# C# Modding Guide

How we write C# code mods for 7 Days to Die. Read this before adding any DLL to a modlet.

> **Game facts this guide is based on (checked 2026-11-22):** the game runs on Unity **2022.3.62f2** using the **Mono** runtime (`MonoBleedingEdge` in the game folder). Game assemblies are in `7DaysToDie_Data/Managed/`. Harmony comes with the game in `Mods/0_TFP_Harmony/`.

---

## 1. Do we need C# at all?

**Default to XML.** Only write C# when XML genuinely can't do the job.

| Use XML when... | Use C# when... |
| --- | --- |
| Adding or changing items, blocks, recipes, loot, traders, buffs, entities, quests | You need behaviour no built-in class or buff trigger supports |
| A built-in class does the job (`PlantGrowing`, `Workstation`, `Loot`...) | You need to change how an existing game system works (AI, damage, crop growth logic) |
| Buffs and `triggered_effect` can express it | You need new UI logic, new console commands, or persistent custom data |

**Why it matters:**

- **Easy Anti-Cheat (EAC):** any mod with a DLL needs EAC **turned off**. XML-only mods work with EAC on.
- **Multiplayer:** DLL mods have to be installed on the server **and every client**.
- **Upkeep:** game updates often rename or change methods, which breaks Harmony patches. XML patches break far less often.

If only part of a feature needs C#, put that part in its own small modlet (for example `BinaryNest_Farming_Code`), so the XML content still works without it.

---

## 2. Runtime and language: what's available

The game runs on **Mono**, not modern .NET. Think "C# around 2019, inside a game loop".

| | Status |
| --- | --- |
| Target framework | **`net48`**. This is what the community uses and it matches the game's assemblies. |
| Modern SDK-style `.csproj`, `dotnet build`, current Visual Studio | ✅ Works |
| Newer C# **syntax** (set `<LangVersion>`): pattern matching, switch expressions, `??=`, local functions, tuples | ✅ Works. The compiler handles it. |
| Features that need **runtime** support: default interface methods, `init` setters, some `Span<T>` APIs | ❌ Avoid |
| .NET 5+ libraries (`System.Text.Json`, ASP.NET-style DI, newer BCL APIs) | ❌ Not available. Only use what's in `Managed/` or packages that target net48 / netstandard2.0 (and ship them with the mod). |
| `async` / `await` | ⚠️ Compiles, but **don't touch game or Unity objects off the main thread**. Use Unity's own patterns instead (see section 6). |

---

## 3. Project setup

### Repo layout

```
BinaryNest7DaysToDieMods/
├── src/
│   ├── BinaryNest.Mods.sln
│   └── BinaryNest.Farming/           # one project per modlet that needs code
│       ├── BinaryNest.Farming.csproj
│       ├── ModApi.cs
│       └── Patches/
└── Mods/
    └── BinaryNest_Farming/           # build output DLL is copied here
```

### `.csproj` template

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net48</TargetFramework>
    <LangVersion>latest</LangVersion>
    <AssemblyName>BinaryNest.Farming</AssemblyName>
    <RootNamespace>BinaryNest.Farming</RootNamespace>
    <Nullable>disable</Nullable>
    <GenerateDocumentationFile>false</GenerateDocumentationFile>
    <!-- Game install. Override per machine with an env var or Directory.Build.props. -->
    <GameDir Condition="'$(GameDir)' == ''">C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die</GameDir>
    <ManagedDir>$(GameDir)\7DaysToDie_Data\Managed</ManagedDir>
    <ModDir>$(MSBuildThisFileDirectory)..\..\Mods\BinaryNest_Farming</ModDir>
  </PropertyGroup>

  <!-- Game references: Private=false means "compile against, never copy". The game already has them. -->
  <ItemGroup>
    <Reference Include="Assembly-CSharp"><HintPath>$(ManagedDir)\Assembly-CSharp.dll</HintPath><Private>false</Private></Reference>
    <Reference Include="LogLibrary"><HintPath>$(ManagedDir)\LogLibrary.dll</HintPath><Private>false</Private></Reference>
    <Reference Include="UnityEngine"><HintPath>$(ManagedDir)\UnityEngine.dll</HintPath><Private>false</Private></Reference>
    <Reference Include="UnityEngine.CoreModule"><HintPath>$(ManagedDir)\UnityEngine.CoreModule.dll</HintPath><Private>false</Private></Reference>
    <Reference Include="0Harmony"><HintPath>$(GameDir)\Mods\0_TFP_Harmony\0Harmony.dll</HintPath><Private>false</Private></Reference>
  </ItemGroup>

  <!-- Copy only our DLL (and pdb) into the modlet folder after build. -->
  <Target Name="CopyToMod" AfterTargets="Build">
    <Copy SourceFiles="$(TargetPath);$(TargetDir)$(TargetName).pdb" DestinationFolder="$(ModDir)" />
  </Target>
</Project>
```

Rules:

- **Never commit or ship game DLLs.** Reference them from the install with `Private=false`.
- Add more `UnityEngine.*Module.dll` references only when you need them (physics, UI, and so on).
- Keep the machine-specific game path overridable. Don't hard-code someone else's drive letter.

### Entry point

The game finds any class that implements `IModApi` in the mod's DLL and calls `InitMod` once on load. It works a lot like a `Startup` / `Program.cs`.

```csharp
using System.Reflection;
using HarmonyLib;

namespace BinaryNest.Farming
{
    public class ModApi : IModApi
    {
        public void InitMod(Mod modInstance)
        {
            Log.Out("[BinaryNest.Farming] Loading");

            var harmony = new Harmony("com.binarynest.farming");
            harmony.PatchAll(Assembly.GetExecutingAssembly());

            // Game lifecycle hooks are on ModEvents (e.g. GameStartDone).
            // Check the exact handler signatures in the decompiled code (they change between versions).
        }
    }
}
```

---

## 4. Harmony patching

Harmony lets us run code **before** or **after** any game method, or **replace** it, without editing game files. It's similar in spirit to middleware or decorators.

```csharp
using HarmonyLib;

namespace BinaryNest.Farming.Patches
{
    // Patch: <GameClass>.<Method>. Find the exact class and method in the decompiler.
    [HarmonyPatch(typeof(SomeGameClass), nameof(SomeGameClass.SomeMethod))]
    public static class SomeGameClass_SomeMethod_Patch
    {
        // Runs before the original. Return false to skip it (use sparingly).
        public static bool Prefix(SomeGameClass __instance) => true;

        // Runs after the original. Can read or modify the result.
        public static void Postfix(ref float __result) { }
    }
}
```

House rules:

1. **Prefer `Postfix` over `Prefix`.** Prefer `Prefix` that returns `true` over one that returns `false`. Skipping the original breaks other mods that patch the same method.
2. **Transpilers (IL rewriting) are a last resort.** They're powerful but fragile, and need a comment explaining what they change and why.
3. **One patch class per patched method.** Name it `<Class>_<Method>_Patch` and keep it in `Patches/`.
4. **Use a unique Harmony ID** for each mod: `com.binarynest.<mod>`.
5. **Fail safe.** If something your patch relies on is missing (an item, a property), log a warning once and let the vanilla behaviour run. Don't throw.
6. **Write down why.** Each patch gets a short comment saying which game behaviour it changes and which feature it supports.

### Reading the game code

Use **ILSpy** or **dnSpy** to open `7DaysToDie_Data/Managed/Assembly-CSharp.dll`. That's how we find the class and method to patch. Don't copy large chunks of decompiled code into the repo. Patch around it instead.

---

## 5. Performance: think like a game developer

In a web app, creating objects freely is fine because .NET's garbage collector is excellent. **Here it isn't.** Mono uses an older, non-generational GC (Boehm), and each collection can pause the game, which players see as a **stutter**. In games, smoothness matters more than average speed.

### Find the hot paths first

Code that runs **every frame**, or **once per entity, block or chunk**, is hot. Examples: `Update` methods, AI ticks, damage calculations, block ticks (crop growth), and anything in chunk generation. Code that runs once (on load, from a console command, on a button click) isn't hot, and normal C# is fine there.

### Rules for hot paths

| Don't | Do |
| --- | --- |
| LINQ (`Where`, `Select`, `ToList`...) | Plain `for` loops |
| `new List<T>()` / `new T[]` per call | Reuse a cached or pooled collection (`list.Clear()`) |
| String concatenation, interpolation, `string.Format` | Build strings only for logging, and only when that log level is on |
| `foreach` over interfaces (`IEnumerable<T>`) | `for` over `List<T>` or arrays |
| Lambdas that capture variables (allocate a closure) | Static methods or cached delegates |
| Boxing (value types into `object`, non-generic collections) | Generic collections and methods |
| Looking up the same item, block or buff by name every call | Look it up once (on init or first use) and cache it |
| `GetComponent<T>()` / `FindObjectOfType` every frame | Cache the reference |
| Exceptions for control flow | Check conditions first (`TryGetValue`, null checks) |

And in patches:

- **Return early.** Check the cheapest "does this apply to me?" condition first (for example "is this one of our blocks?") and get out.
- **Do the minimum.** A Postfix on a method called 10,000 times a frame costs 10,000× whatever you put in it.
- **Measure when unsure.** A temporary `Stopwatch` with a log summary every N calls is fine while developing. Remove it before release.

---

## 6. Threading and async

- **Unity and game objects are main-thread only.** Touching entities, blocks, the world or UI from another thread can crash the game or cause subtle bugs.
- Avoid `Task.Run` / `async` work that touches game state. If background work is really needed (heavy computation on plain data), do the computation off-thread and hand the **result** back to the main thread to apply.
- For "do this over several frames" or "do this in N seconds", use the game's own update hooks or Unity coroutines instead of `Task.Delay`.

---

## 7. Logging and debugging

- Use the game's logger: `Log.Out(...)`, `Log.Warning(...)`, `Log.Error(...)`.
- **Always prefix messages** with the mod: `[BinaryNest.Farming] ...`, so they're easy to filter.
- Output appears in the `F1` console and in the game's log file (`%AppData%\7DaysToDie\logs\`, or the `output_log` next to the game).
- **Never log in hot paths** in release builds. If you need debug logging, put it behind a flag.
- Ship the `.pdb` during development so exceptions show line numbers.

---

## 8. Compatibility and multiplayer

- **Server vs client:** work out where your code needs to run. Game logic (crop growth, loot, AI) is usually decided by the server. Visuals and UI run on the client. Guard code where needed so it doesn't run twice or in the wrong place.
- **Saves:** if the mod stores custom data, plan what happens when the mod is removed from an existing save. It should never corrupt the world.
- **Other mods:** keep patches minimal and non-destructive (see the Harmony rules) so other mods patching the same methods keep working.
- **Game updates:** after every game update, rebuild against the new DLLs and test all patches. Write the tested game version in `ModInfo.xml` and the mod README.

---

## 9. Pre-release checklist for a code mod

- [ ] The feature can't reasonably be done in XML (or the XML part is split into its own modlet).
- [ ] Builds against the **current** game DLLs with no warnings you haven't checked.
- [ ] No game DLLs in the mod folder or the repo.
- [ ] Every Harmony patch has a comment explaining what and why. No unexplained `Prefix → false` or transpilers.
- [ ] Hot paths reviewed against section 5 (no allocations, lookups cached, early returns).
- [ ] No game state touched off the main thread.
- [ ] Logs are prefixed, and there's no logging in hot paths.
- [ ] Tested in single player **and** on a dedicated server with a client connected.
- [ ] Tested adding the mod to an existing save, and removing it.
- [ ] Mod README says **EAC must be off** and lists the tested game version.
