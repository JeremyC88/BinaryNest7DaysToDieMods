// Builds the Adapting Farming asset bundle from the FBX models in Assets/Farming.
//
// Run headless from the repo root:
//   "C:\Program Files\Unity\Hub\Editor\2022.3.62f2\Editor\Unity.exe" -batchmode -quit -nographics
//     -projectPath unity/BinaryNestModAssets -executeMethod BinaryNest.Editor.FarmingBundleBuilder.Build
//     -logFile -
// or from the Unity menu: BinaryNest > Build Farming Bundle.
//
// For every model listed in Models it:
//   1. sets the FBX import settings and maps its materials to ours,
//   2. builds a prefab laid out like the game's own plant prefabs,
//   3. builds all prefabs into BinaryNestFarming.unity3d and copies it into
//      Mods/BinaryNest_Farming/Resources.
//
// The blocks.xml reference for a prefab is:
//   #@modfolder:Resources/BinaryNestFarming.unity3d?<PrefabName>

using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace BinaryNest.Editor
{
    public static class FarmingBundleBuilder
    {
        const string BundleName = "BinaryNestFarming.unity3d";
        const string FarmingRoot = "Assets/Farming";
        const string BuildDir = "AssetBundles";

        // Same layer the game's own plant prefabs use on their root object.
        // (The game resets the collider layer when it spawns the block anyway.)
        const int GamePlantLayer = 16;

        // The game only treats a hit collider as a model block (so it can be
        // aimed at, named and harvested) when its tag is "T_Block". See
        // Voxel.raycastNew -> GameUtils.FindMasterBlockForEntityModelBlock.
        //
        // Bundles store tags as a POSITION in the project's tag list, not by
        // name. All of the game's plant prefabs use custom tag position 4, so
        // T_Block must be at position 4 in this project's tag list too.
        const string BlockTag = "T_Block";
        const int GameBlockTagIndex = 4;
        static readonly string[] GameTagLayout =
        {
            // Positions 0-3 are other game tags we don't use; the names here
            // are placeholders that only reserve the slots.
            "GameTag0", "GameTag1", "GameTag2", "GameTag3",
            BlockTag,
        };

        // Model (FBX) name -> prefab name used in blocks.xml.
        static readonly (string crop, string model, string prefab)[] Models =
        {
            ("Carrot", "CarrotSeedling", "CarrotSeedling"),
            ("Carrot", "CarrotGrowth",   "CarrotGrowth"),
            ("Carrot", "CarrotHarvest",  "CarrotHarvest"),
            ("Wheat",  "WheatSeedling",  "WheatSeedling"),
            ("Wheat",  "WheatGrowth",    "WheatGrowth"),
            ("Wheat",  "WheatHarvest",   "WheatHarvest"),
        };

        // Per crop: material name in the FBX -> colour, smoothness, optional
        // texture (relative to Assets/Farming/<crop>/Textures) and whether it's
        // a cut-out leaf card (texture alpha cuts out the leaf, both sides drawn,
        // like the vanilla potato and blueberry leaves). Colours match the
        // Blender build scripts (sRGB). Textured materials use white so the
        // texture's own colours show.
        static readonly Dictionary<string, Dictionary<string, (Color color, float smoothness, string texture, bool cutout)>> MaterialDefs = new()
        {
            ["Carrot"] = new()
            {
                ["CarrotLeaf"]  = (Color.white, 0.15f, "CarrotFrond.png", true),
                ["CarrotStalk"] = (new Color(0.17f, 0.29f, 0.10f), 0.10f, null, false),
                ["CarrotRoot"]  = (new Color(0.80f, 0.32f, 0.05f), 0.30f, null, false),
            },
            ["Wheat"] = new()
            {
                ["WheatPlant"]      = (Color.white, 0.15f, "WheatPlant.png", false),
                ["WheatGrainGreen"] = (new Color(0.45f, 0.53f, 0.23f), 0.25f, null, false),
                ["WheatGrainGold"]  = (new Color(0.80f, 0.62f, 0.30f), 0.30f, null, false),
            },
        };

        // All crop materials use our wind shader (Assets/Farming/Shaders/CropWind.shader),
        // which sways with the game's global _Wind like the vanilla plants.
        const string CropShader = "BinaryNest/CropWind";

        // Per crop wind tuning:
        //   height   - height (m) at which a plant sways fully (roots don't move)
        //   strength - how far (m) the tips move in normal wind
        //   flutter  - small fast leaf/ear movement (m)
        static readonly Dictionary<string, (float height, float strength, float flutter)> SwayDefs = new()
        {
            ["Carrot"] = (0.40f, 0.045f, 0.004f),   // low, leafy tops: gentle
            ["Wheat"]  = (0.95f, 0.085f, 0.003f),   // tall, flexible stalks: more movement
        };

        [MenuItem("BinaryNest/Build Farming Bundle")]
        public static void Build()
        {
            if (!EnsureGameTags())
                return;

            var prefabPaths = new List<string>();
            foreach (var (crop, model, prefab) in Models)
            {
                var fbxPath = $"{FarmingRoot}/{crop}/Models/{model}.fbx";
                if (!File.Exists(fbxPath))
                {
                    Debug.LogError($"[BinaryNest] Missing model {fbxPath}. Run the Blender build script first.");
                    continue;
                }
                ConfigureImporter(fbxPath, crop);
                prefabPaths.Add(BuildPrefab(fbxPath, crop, prefab));
            }

            if (prefabPaths.Count == 0)
            {
                Debug.LogError("[BinaryNest] Nothing to build.");
                return;
            }

            Directory.CreateDirectory(BuildDir);
            var build = new AssetBundleBuild
            {
                assetBundleName = BundleName,
                assetNames = prefabPaths.ToArray(),
            };
            var manifest = BuildPipeline.BuildAssetBundles(
                BuildDir, new[] { build },
                BuildAssetBundleOptions.ChunkBasedCompression | BuildAssetBundleOptions.StrictMode,
                BuildTarget.StandaloneWindows64);
            if (manifest == null)
            {
                Debug.LogError("[BinaryNest] Asset bundle build failed.");
                return;
            }

            var modResources = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "..", "Mods", "BinaryNest_Farming", "Resources"));
            Directory.CreateDirectory(modResources);
            var src = Path.Combine(BuildDir, BundleName.ToLowerInvariant());
            if (!File.Exists(src)) src = Path.Combine(BuildDir, BundleName);
            var dst = Path.Combine(modResources, BundleName);
            File.Copy(src, dst, true);
            Debug.Log($"[BinaryNest] Built {prefabPaths.Count} prefabs into {dst} ({new FileInfo(dst).Length / 1024} KB)");

            VerifyTagsAgainstGame(dst);
        }

        // Loads a vanilla plant prefab from the game install and our built bundle,
        // and checks both roots resolve to T_Block in this project. If they do, our
        // tag sits at the same position as the game's.
        const string GamePlantsBundle = @"C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die\Data\Addressables\Standalone\automatic_assets_entities\plants.bundle";

        static void VerifyTagsAgainstGame(string ourBundlePath)
        {
            if (!File.Exists(GamePlantsBundle))
            {
                Debug.LogWarning("[BinaryNest] Game install not found; skipped the tag check against vanilla plants.");
                return;
            }
            AssetBundle game = null, ours = null;
            try
            {
                game = AssetBundle.LoadFromFile(GamePlantsBundle);
                ours = AssetBundle.LoadFromFile(ourBundlePath);
                var vanilla = game.LoadAsset<GameObject>("Assets/AssetBundles/Automatic/Entities/Plants/potato_plant_harvestPrefab.prefab");
                var vanillaTag = vanilla ? vanilla.tag : "<missing>";
                var ok = vanillaTag == BlockTag;
                foreach (var go in ours.LoadAllAssets<GameObject>())
                {
                    var match = go.tag == vanillaTag;
                    ok &= match;
                    var shaders = go.GetComponentsInChildren<Renderer>(true)
                        .SelectMany(r => r.sharedMaterials)
                        .Where(m => m != null && m.shader != null)
                        .Select(m => $"{m.shader.name}{(m.shader.isSupported ? "" : " (NOT SUPPORTED)")}")
                        .Distinct();
                    Debug.Log($"[BinaryNest] Shader check: {go.name} uses {string.Join(", ", shaders)}");
                    var lods = go.GetComponent<LODGroup>();
                    Debug.Log($"[BinaryNest] Tag check: {go.name} = '{go.tag}', vanilla potato = '{vanillaTag}' -> {(match ? "match" : "MISMATCH")}; root LODGroup: {(lods ? lods.lodCount + " LODs" : "none")}");
                }
                if (ok) Debug.Log("[BinaryNest] Tag check passed.");
                else Debug.LogError("[BinaryNest] Tag check FAILED: prefabs will not be targetable in game.");
            }
            finally
            {
                if (ours) ours.Unload(true);
                if (game) game.Unload(true);
            }
        }

        // Makes the project's tag list start with GameTagLayout, so "T_Block"
        // is stored at the same position the game expects.
        static bool EnsureGameTags()
        {
            var tagManager = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);
            var tags = tagManager.FindProperty("tags");
            var changed = false;
            for (int i = 0; i < GameTagLayout.Length; i++)
            {
                if (i >= tags.arraySize)
                {
                    tags.InsertArrayElementAtIndex(i);
                    changed = true;
                }
                var element = tags.GetArrayElementAtIndex(i);
                if (element.stringValue != GameTagLayout[i])
                {
                    if (i == GameBlockTagIndex || string.IsNullOrEmpty(element.stringValue) || element.stringValue.StartsWith("GameTag"))
                    {
                        element.stringValue = GameTagLayout[i];
                        changed = true;
                    }
                    else
                    {
                        Debug.LogError($"[BinaryNest] Tag slot {i} holds '{element.stringValue}', but the game layout needs '{GameTagLayout[i]}' there. Fix the tag list before building.");
                        return false;
                    }
                }
            }
            if (changed)
            {
                tagManager.ApplyModifiedPropertiesWithoutUndo();
                AssetDatabase.SaveAssets();
                Debug.Log("[BinaryNest] Updated the tag list to match the game's layout.");
            }

            var actual = tags.GetArrayElementAtIndex(GameBlockTagIndex).stringValue;
            if (actual != BlockTag)
            {
                Debug.LogError($"[BinaryNest] Tag slot {GameBlockTagIndex} is '{actual}', expected '{BlockTag}'.");
                return false;
            }
            return true;
        }

        static void ConfigureImporter(string fbxPath, string crop)
        {
            var importer = (ModelImporter)AssetImporter.GetAtPath(fbxPath);
            importer.globalScale = 1f;
            importer.useFileScale = true;
            importer.importAnimation = false;
            importer.animationType = ModelImporterAnimationType.None;
            importer.importCameras = false;
            importer.importLights = false;
            importer.isReadable = false;
            importer.meshCompression = ModelImporterMeshCompression.Off;
            importer.importNormals = ModelImporterNormals.Import;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            importer.materialLocation = ModelImporterMaterialLocation.InPrefab;

            foreach (var (name, def) in MaterialDefs[crop])
            {
                var mat = GetOrCreateMaterial(crop, name, def.color, def.smoothness, def.texture, def.cutout);
                importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), name), mat);
            }
            importer.SaveAndReimport();
        }

        static Texture2D ConfigureTexture(string crop, string file, bool cutout)
        {
            var path = $"{FarmingRoot}/{crop}/Textures/{file}";
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null)
            {
                Debug.LogError($"[BinaryNest] Missing texture {path}. Run the Blender build script first.");
                return null;
            }
            importer.textureType = TextureImporterType.Default;
            importer.sRGBTexture = true;
            importer.mipmapEnabled = true;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.filterMode = FilterMode.Bilinear;
            if (cutout)
            {
                // Keep the alpha that cuts out the leaf, and keep leaves from
                // thinning out in the smaller mipmaps used at a distance.
                importer.alphaSource = TextureImporterAlphaSource.FromInput;
                importer.alphaIsTransparency = true;
                importer.mipMapsPreserveCoverage = true;
                importer.alphaTestReferenceValue = 0.5f;
            }
            else
            {
                importer.alphaSource = TextureImporterAlphaSource.None;
            }
            importer.textureCompression = TextureImporterCompression.Compressed;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        static Material GetOrCreateMaterial(string crop, string name, Color color, float smoothness, string texture, bool cutout)
        {
            var dir = $"{FarmingRoot}/{crop}/Materials";
            Directory.CreateDirectory(dir);
            var path = $"{dir}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            var shader = Shader.Find(CropShader);
            if (shader == null)
            {
                Debug.LogError($"[BinaryNest] Shader '{CropShader}' not found; falling back to Standard (no wind sway).");
                shader = Shader.Find("Standard");
            }
            if (mat == null)
            {
                mat = new Material(shader);
                AssetDatabase.CreateAsset(mat, path);
            }
            mat.shader = shader;
            mat.color = color;
            mat.mainTexture = texture != null ? ConfigureTexture(crop, texture, cutout) : null;
            // Cut-out leaf cards: alpha test, both sides drawn. Solid parts: opaque queue.
            mat.SetFloat("_Cutoff", cutout ? 0.5f : 0f);
            mat.SetFloat("_Cull", cutout ? (float)UnityEngine.Rendering.CullMode.Off : (float)UnityEngine.Rendering.CullMode.Back);
            mat.renderQueue = cutout ? (int)UnityEngine.Rendering.RenderQueue.AlphaTest : (int)UnityEngine.Rendering.RenderQueue.Geometry;
            mat.SetFloat("_Glossiness", smoothness);
            mat.SetFloat("_Metallic", 0f);
            if (SwayDefs.TryGetValue(crop, out var sway))
            {
                mat.SetFloat("_SwayHeight", sway.height);
                mat.SetFloat("_SwayStrength", sway.strength);
                mat.SetFloat("_Flutter", sway.flutter);
            }
            mat.enableInstancing = true;
            EditorUtility.SetDirty(mat);
            return mat;
        }

        // Layout copied from the game's plant prefabs (e.g. potato_plant_harvestPrefab):
        //   <Prefab>        root, layer 16, tag T_Block, collider around the base of the plant
        //     <Model>       the mesh, moved down 0.5 so it sits on the bottom of the block
        static string BuildPrefab(string fbxPath, string crop, string prefabName)
        {
            var modelAsset = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);

            var root = new GameObject(prefabName) { layer = GamePlantLayer, tag = BlockTag };
            var model = (GameObject)PrefabUtility.InstantiatePrefab(modelAsset);
            PrefabUtility.UnpackPrefabInstance(model, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            model.name = "Model";
            model.transform.SetParent(root.transform, false);
            model.transform.localPosition = new Vector3(0f, -0.5f, 0f);

            // Collider sized from the mesh, like the vanilla SphereCollider (r 0.3, centre y -0.1).
            var bounds = new Bounds(model.transform.localPosition, Vector3.zero);
            foreach (var r in model.GetComponentsInChildren<Renderer>())
            {
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
                r.receiveShadows = true;
                bounds.Encapsulate(r.bounds);
            }
            var collider = root.AddComponent<SphereCollider>();
            var horizontal = Mathf.Max(bounds.extents.x, bounds.extents.z);
            collider.radius = Mathf.Clamp(Mathf.Max(horizontal * 0.6f, bounds.extents.y), 0.15f, 0.4f);
            collider.center = new Vector3(0f, -0.5f + Mathf.Max(bounds.extents.y, 0.1f), 0f);

            var lodSummary = SetUpLods(root, model);

            var dir = $"{FarmingRoot}/{crop}/Prefabs";
            Directory.CreateDirectory(dir);
            var path = $"{dir}/{prefabName}.prefab";
            var summary = $"mesh size {bounds.size}, collider r={collider.radius:F2} centre={collider.center}, {lodSummary}";
            PrefabUtility.SaveAsPrefabAsset(root, path);
            Object.DestroyImmediate(root);

            Debug.Log($"[BinaryNest] Prefab {path}: {summary}");
            return path;
        }

        // Screen-height thresholds for switching away from each LOD (LOD0, LOD1, ...).
        // The game recalculates the last one (when the plant is culled) from the
        // plant's size, so only the earlier switches really come from here.
        static readonly float[] LodTransitions = { 0.30f, 0.12f, 0.03f };

        // The game reads the LODGroup from the prefab ROOT (BlockShapeModelEntity
        // .PoolCreateCallBack), like the vanilla yucca and cotton prefabs. Unity
        // auto-creates one on the imported model from the _LOD0/_LOD1/... mesh
        // names, so move it to the root.
        static string SetUpLods(GameObject root, GameObject model)
        {
            foreach (var g in model.GetComponentsInChildren<LODGroup>(true))
                Object.DestroyImmediate(g);

            var levels = new List<LOD>();
            for (int i = 0; ; i++)
            {
                var renderers = model.GetComponentsInChildren<Renderer>(true)
                    .Where(r => r.name.EndsWith($"_LOD{i}"))
                    .ToArray();
                if (renderers.Length == 0) break;
                var height = i < LodTransitions.Length ? LodTransitions[i] : LodTransitions[^1] * 0.5f;
                levels.Add(new LOD(height, renderers));
            }

            if (levels.Count == 0)
                return "no LODs";

            var group = root.AddComponent<LODGroup>();
            group.fadeMode = LODFadeMode.CrossFade;
            group.animateCrossFading = true;
            group.SetLODs(levels.ToArray());
            group.RecalculateBounds();
            return $"{levels.Count} LODs";
        }
    }
}
