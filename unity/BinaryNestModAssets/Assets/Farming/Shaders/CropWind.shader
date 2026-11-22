// Crop shader for BinaryNest farming plants: Standard lighting plus wind sway.
//
// The game sets a global shader vector every frame (WeatherManager):
//     _Wind = (windSpeed, windTime, previousWindSpeed, previousWindTime)
// windSpeed includes gusts and follows the weather; windTime is a clock that
// runs faster in stronger wind. Reading it keeps our crops swaying with the
// same weather as the vanilla plants. Outside the game (_Wind = 0) the plants
// still sway gently from _SwayIdle, so they never look frozen.
//
// Sway is applied in world space, weighted by height above the object's
// origin (the plant's base), so roots stay put and tips move the most. Each
// plant gets its own phase from its position, so a field doesn't move in
// lockstep.
Shader "BinaryNest/CropWind"
{
    Properties
    {
        _Color ("Color", Color) = (1, 1, 1, 1)
        _MainTex ("Albedo", 2D) = "white" {}
        _Glossiness ("Smoothness", Range(0, 1)) = 0.2
        _Metallic ("Metallic", Range(0, 1)) = 0

        [Header(Wind)]
        _SwayHeight ("Full sway at height (m)", Float) = 0.5
        _SwayStrength ("Sway distance (m)", Float) = 0.05
        _SwayIdle ("Sway when calm (0-1)", Float) = 0.25
        _SwaySpeed ("Sway speed", Float) = 1.3
        _Flutter ("Leaf flutter (m)", Float) = 0.004
    }

    SubShader
    {
        // Batching would merge plants and lose each plant's own origin.
        Tags { "RenderType" = "Opaque" "DisableBatching" = "True" }
        LOD 200

        CGPROGRAM
        #pragma surface surf Standard vertex:vert addshadow fullforwardshadows
        #pragma multi_compile_instancing
        #pragma target 3.0

        sampler2D _MainTex;
        fixed4 _Color;
        half _Glossiness;
        half _Metallic;
        float _SwayHeight;
        float _SwayStrength;
        float _SwayIdle;
        float _SwaySpeed;
        float _Flutter;

        // Global, set by the game (see header).
        float4 _Wind;

        struct Input
        {
            float2 uv_MainTex;
        };

        void vert(inout appdata_full v)
        {
            float3 worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
            float3 origin = float3(unity_ObjectToWorld._m03, unity_ObjectToWorld._m13, unity_ObjectToWorld._m23);

            // 0 at the base, 1 at _SwayHeight and above; squared so the stem bends smoothly.
            float h = saturate((worldPos.y - origin.y) / max(_SwayHeight, 0.01));
            h *= h;

            float windSpeed = saturate(_Wind.x);
            float phase = dot(origin.xz, float2(0.73, 1.37));
            float t = _Time.y * _SwaySpeed + _Wind.y * 8.0 + phase;

            // Main sway: two mixed waves, plus a lean with the wind.
            float strength = _SwayStrength * (_SwayIdle + windSpeed * 3.0);
            float bend = sin(t) * 0.7 + sin(t * 2.3 + 1.7) * 0.3 + windSpeed * 0.8;
            float2 dir = float2(0.8, 0.6);
            float2 offset = dir * bend * strength * h;

            // Small, fast flutter that differs per vertex (leaves and ears).
            float flutter = sin(_Time.y * 7.0 + dot(worldPos, float3(23.0, 17.0, 19.0)))
                            * _Flutter * h * (0.3 + windSpeed * 2.0);

            worldPos.xz += offset + flutter;
            worldPos.y -= length(offset) * 0.3 * h;   // tips dip slightly as they bend

            v.vertex.xyz = mul(unity_WorldToObject, float4(worldPos, 1.0)).xyz;
        }

        void surf(Input IN, inout SurfaceOutputStandard o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            o.Albedo = c.rgb;
            o.Metallic = _Metallic;
            o.Smoothness = _Glossiness;
            o.Alpha = 1.0;
        }
        ENDCG
    }

    FallBack "Diffuse"
}
