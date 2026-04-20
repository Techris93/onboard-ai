// Vertex shader - passes through position and UV
export const oceanVertexShader = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position, 1.0);
  }
`;

// Fragment shader - full ocean simulation with waves, foam, shoreline, lighting
export const oceanFragmentShader = /* glsl */ `
  precision highp float;

  uniform float uTime;
  uniform vec2 uResolution;
  uniform vec2 uMouse;
  uniform float uMouseActive;
  uniform float uIntensity;
  uniform float uSunPositionX;
  uniform float uSunPositionY;

  varying vec2 vUv;

  // Hash function for noise
  float hash(vec2 p) {
    float h = dot(p, vec2(127.1, 311.7));
    return fract(sin(h) * 43758.5453123);
  }

  // Value noise
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
  }

  // Fractional Brownian Motion
  float fbm(vec2 p, int octaves) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;
    for (int i = 0; i < 6; i++) {
      if (i >= octaves) break;
      value += amplitude * noise(p * frequency);
      amplitude *= 0.5;
      frequency *= 2.0;
    }
    return value;
  }

  // Wave function - combines multiple wave layers
  float waveHeight(vec2 pos, float t) {
    float h = 0.0;

    // Large swells
    float large = fbm(pos * 0.8 + vec2(t * 0.15, t * 0.05), 4);
    h += large * 0.4 * uIntensity;

    // Medium waves
    float medium = fbm(pos * 2.0 + vec2(t * 0.25, -t * 0.12), 3);
    h += medium * 0.25 * uIntensity;

    // Small chop
    float small = fbm(pos * 5.0 + vec2(t * 0.4, t * 0.2), 3);
    h += small * 0.1 * uIntensity;

    // Detail ripples
    float detail = fbm(pos * 12.0 + vec2(t * 0.6, -t * 0.3), 2);
    h += detail * 0.04 * uIntensity;

    return h;
  }

  // Compute wave normal from finite differences
  vec3 waveNormal(vec2 pos, float t) {
    float eps = 0.01;
    float h = waveHeight(pos, t);
    float hx = waveHeight(pos + vec2(eps, 0.0), t);
    float hy = waveHeight(pos + vec2(0.0, eps), t);
    return normalize(vec3(-(hx - h) / eps, -(hy - h) / eps, 1.0));
  }

  // Foam mask - where waves are breaking
  float foamMask(vec2 pos, float t) {
    float n1 = fbm(pos * 8.0 + vec2(t * 0.3, t * 0.15), 3);
    float n2 = fbm(pos * 15.0 + vec2(-t * 0.25, t * 0.35), 2);
    float mask = smoothstep(0.45, 0.65, n1 * 0.6 + n2 * 0.4);
    // Waves break more at peaks
    float height = waveHeight(pos, t);
    mask *= smoothstep(0.1, 0.5, height);
    return mask * uIntensity;
  }

  // Shoreline foam
  float shorelineFoam(vec2 pos, float t) {
    // Shoreline at bottom ~30% of screen
    float shoreDist = pos.y;
    float waterline = 0.25 + sin(pos.x * 4.0 + t * 0.5) * 0.02
                           + sin(pos.x * 8.0 - t * 0.8) * 0.01;

    // Wet sand band
    float wetSand = smoothstep(waterline - 0.05, waterline, shoreDist);

    // Foam streaks
    float foamNoise = fbm(vec2(pos.x * 20.0, shoreDist * 30.0) + vec2(t * 0.8, 0.0), 3);
    float streaks = smoothstep(0.5, 0.7, foamNoise) * smoothstep(waterline + 0.02, waterline, shoreDist);
    streaks *= smoothstep(waterline - 0.08, waterline - 0.02, shoreDist);

    // Wave run-up
    float runup = smoothstep(waterline, waterline + 0.03, shoreDist)
                * smoothstep(waterline + 0.06, waterline + 0.03, shoreDist);
    runup *= 0.5 + 0.5 * sin(pos.x * 15.0 + t * 2.0);

    return max(streaks, runup) * 0.8;
  }

  // Mouse wake - frothy trail behind cursor
  float mouseWake(vec2 pos, float t) {
    if (uMouseActive < 0.5) return 0.0;

    vec2 mouseUV = uMouse;
    float dist = length(pos - mouseUV);

    // Wake radius
    float wake = smoothstep(0.12, 0.0, dist);

    // Turbulence
    float turb = fbm(pos * 25.0 + vec2(t * 2.0), 2);
    wake *= 0.6 + 0.4 * turb;

    return wake * uMouseActive;
  }

  // Time of day colors
  void timeOfDay(float cycle, out vec3 skyColor, out vec3 sunColor,
                 out vec3 ambientColor, out vec3 fogColor, out float fogDensity,
                 out vec3 waterDeep, out vec3 waterShallow) {
    // Slow cycle: 0=midnight, 0.25=dawn, 0.5=day, 0.75=golden, 1.0=midnight
    float t = fract(cycle);

    // Midnight
    vec3 midSky = vec3(0.02, 0.03, 0.06);
    vec3 midSun = vec3(0.3, 0.35, 0.5);
    vec3 midAmb = vec3(0.01, 0.02, 0.04);
    vec3 midFog = vec3(0.02, 0.04, 0.08);
    vec3 midDeep = vec3(0.02, 0.04, 0.08);
    vec3 midShal = vec3(0.05, 0.1, 0.18);

    // Dawn
    vec3 dawnSky = vec3(0.15, 0.25, 0.45);
    vec3 dawnSun = vec3(1.0, 0.65, 0.35);
    vec3 dawnAmb = vec3(0.08, 0.1, 0.15);
    vec3 dawnFog = vec3(0.15, 0.2, 0.35);
    vec3 dawnDeep = vec3(0.08, 0.15, 0.3);
    vec3 dawnShal = vec3(0.2, 0.35, 0.55);

    // Day
    vec3 daySky = vec3(0.25, 0.4, 0.6);
    vec3 daySun = vec3(1.0, 0.95, 0.85);
    vec3 dayAmb = vec3(0.1, 0.18, 0.28);
    vec3 dayFog = vec3(0.15, 0.25, 0.4);
    vec3 dayDeep = vec3(0.1, 0.25, 0.4);
    vec3 dayShal = vec3(0.25, 0.5, 0.65);

    // Golden hour
    vec3 goldSky = vec3(0.5, 0.3, 0.15);
    vec3 goldSun = vec3(1.0, 0.55, 0.15);
    vec3 goldAmb = vec3(0.2, 0.12, 0.05);
    vec3 goldFog = vec3(0.3, 0.2, 0.08);
    vec3 goldDeep = vec3(0.2, 0.1, 0.04);
    vec3 goldShal = vec3(0.5, 0.3, 0.12);

    // Interpolate between keyframes
    if (t < 0.25) {
      float f = t / 0.25;
      skyColor = mix(midSky, dawnSky, f);
      sunColor = mix(midSun, dawnSun, f);
      ambientColor = mix(midAmb, dawnAmb, f);
      fogColor = mix(midFog, dawnFog, f);
      waterDeep = mix(midDeep, dawnDeep, f);
      waterShallow = mix(midShal, dawnShal, f);
      fogDensity = mix(0.15, 0.1, f);
    } else if (t < 0.5) {
      float f = (t - 0.25) / 0.25;
      skyColor = mix(dawnSky, daySky, f);
      sunColor = mix(dawnSun, daySun, f);
      ambientColor = mix(dawnAmb, dayAmb, f);
      fogColor = mix(dawnFog, dayFog, f);
      waterDeep = mix(dawnDeep, dayDeep, f);
      waterShallow = mix(dawnShal, dayShal, f);
      fogDensity = mix(0.1, 0.12, f);
    } else if (t < 0.75) {
      float f = (t - 0.5) / 0.25;
      skyColor = mix(daySky, goldSky, f);
      sunColor = mix(daySun, goldSun, f);
      ambientColor = mix(dayAmb, goldAmb, f);
      fogColor = mix(dayFog, goldFog, f);
      waterDeep = mix(dayDeep, goldDeep, f);
      waterShallow = mix(dayShal, goldShal, f);
      fogDensity = mix(0.12, 0.15, f);
    } else {
      float f = (t - 0.75) / 0.25;
      skyColor = mix(goldSky, midSky, f);
      sunColor = mix(goldSun, midSun, f);
      ambientColor = mix(goldAmb, midAmb, f);
      fogColor = mix(goldFog, midFog, f);
      waterDeep = mix(goldDeep, midDeep, f);
      waterShallow = mix(goldShal, midShal, f);
      fogDensity = mix(0.15, 0.15, f);
    }
  }

  void main() {
    vec2 uv = vUv;
    vec2 pos = uv;

    // Aspect correction
    float aspect = uResolution.x / uResolution.y;
    pos.x *= aspect;

    // Time
    float t = uTime;

    // Time of day
    float cycle = t * 0.005;
    vec3 skyColor, sunColor, ambientColor, fogColor, waterDeep, waterShallow;
    float fogDensity;
    timeOfDay(cycle, skyColor, sunColor, ambientColor, fogColor, fogDensity, waterDeep, waterShallow);

    // Wave simulation
    float height = waveHeight(pos, t);
    vec3 normal = waveNormal(pos, t);

    // View direction (from above, slight tilt)
    vec3 viewDir = normalize(vec3(0.0, 0.5, 1.0));

    // Sun direction
    vec3 sunDir = normalize(vec3(uSunPositionX, uSunPositionY, 1.0));

    // Fresnel
    float fresnel = pow(1.0 - max(0.0, dot(viewDir, normal)), 5.0);

    // Water color base
    vec3 waterColor = mix(waterDeep, waterShallow, height * 2.0 + 0.5);

    // Reflection
    vec3 reflectDir = reflect(-sunDir, normal);
    float spec = pow(max(0.0, dot(reflectDir, viewDir)), 300.0);

    // Sun reflection color
    vec3 reflection = sunColor * spec * 2.0;

    // Sky reflection on water
    vec3 skyReflection = mix(skyColor, sunColor, fresnel * 0.5);

    // Combine
    vec3 color = mix(waterColor + ambientColor * 0.5, skyReflection, fresnel * 0.7);
    color += reflection;

    // Foam
    float foam = foamMask(pos, t);
    vec3 foamColor = vec3(0.95, 0.95, 0.92);
    color = mix(color, foamColor, foam * 0.6);

    // Shoreline
    float shore = shorelineFoam(uv, t);
    color = mix(color, foamColor * 0.9, shore);

    // Wet sand at very bottom
    float sandLine = 0.22 + sin(uv.x * 6.0 + t * 0.3) * 0.015;
    float sandMask = smoothstep(sandLine + 0.03, sandLine, uv.y);
    vec3 sandColor = vec3(0.12, 0.1, 0.07);
    vec3 wetSandColor = vec3(0.06, 0.08, 0.12);
    float wetness = smoothstep(sandLine, sandLine - 0.06, uv.y);
    color = mix(color, mix(sandColor, wetSandColor, wetness), sandMask);

    // Mouse wake
    float wake = mouseWake(uv, t);
    color = mix(color, foamColor, wake * 0.4);

    // Add wake displacement (brighten nearby water)
    color += vec3(0.05, 0.05, 0.08) * wake;

    // Fog
    float fogFactor = 1.0 - exp(-uv.y * uv.y * fogDensity * fogDensity * 4.0);
    color = mix(color, fogColor, fogFactor * 0.3);

    // Vignette
    vec2 vigUV = uv - 0.5;
    float vignette = 1.0 - dot(vigUV, vigUV) * 0.5;
    color *= vignette;

    // Tonemap (simple ACES approximation)
    color = color * (2.51 * color + 0.03) / (color * (2.43 * color + 0.59) + 0.14);

    gl_FragColor = vec4(color, 1.0);
  }
`;
