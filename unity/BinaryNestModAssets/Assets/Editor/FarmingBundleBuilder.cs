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
        const int GamePlantLayer = 16;

        // Model (FBX) name -> prefab name used in blocks.xml.
        static readonly (string crop, string model, string prefab)[] Models =
        {
            ("Carrot", "CarrotSeedling", "CarrotSeedling"),
            ("Carrot", "CarrotGrowth",   "CarrotGrowth"),
            ("Carrot", "CarrotHarvest",  "CarrotHarvest"),
        };

        // Material name in the FBX -> colour and smoothness.
        static readonly Dictionary<string, (Color color, float smoothness)> MaterialDefs = new()
        {
            ["CarrotLeaf"]  = (new Color(0.13f, 0.38f, 0.08f), 0.25f),
            ["CarrotStalk"] = (new Color(0.30f, 0.52f, 0.16f), 0.20f),
            ["CarrotRoot"]  = (new Color(0.88f, 0.36f, 0.05f), 0.35f),
        };

        [MenuItem("BinaryNest/Build Farming Bundle")]
        public static void Build()
        {
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

            foreach (var (name, def) in MaterialDefs)
            {
                var mat = GetOrCreateMaterial(crop, name, def.color, def.smoothness);
                importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material), name), mat);
            }
            importer.SaveAndReimport();
        }

        static Material GetOrCreateMaterial(string crop, string name, Color color, float smoothness)
        {
            var dir = $"{FarmingRoot}/{crop}/Materials";
            Directory.CreateDirectory(dir);
            var path = $"{dir}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null)
            {
                mat = new Material(Shader.Find("Standard"));
                AssetDatabase.CreateAsset(mat, path);
            }
            mat.shader = Shader.Find("Standard");
            mat.color = color;
            mat.SetFloat("_Glossiness", smoothness);
            mat.SetFloat("_Metallic", 0f);
            mat.enableInstancing = true;
            EditorUtility.SetDirty(mat);
            return mat;
        }

        // Layout copied from the game's plant prefabs (e.g. potato_plant_harvestPrefab):
        //   <Prefab>        root, layer 16, collider around the base of the plant
        //     <Model>       the mesh, moved down 0.5 so it sits on the bottom of the block
        static string BuildPrefab(string fbxPath, string crop, string prefabName)
        {
            var modelAsset = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);

            var root = new GameObject(prefabName) { layer = GamePlantLayer };
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

            var dir = $"{FarmingRoot}/{crop}/Prefabs";
            Directory.CreateDirectory(dir);
            var path = $"{dir}/{prefabName}.prefab";
            var summary = $"mesh size {bounds.size}, collider r={collider.radius:F2} centre={collider.center}";
            PrefabUtility.SaveAsPrefabAsset(root, path);
            Object.DestroyImmediate(root);

            Debug.Log($"[BinaryNest] Prefab {path}: {summary}");
            return path;
        }
    }
}
