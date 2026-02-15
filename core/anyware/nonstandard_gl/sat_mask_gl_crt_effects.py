from __future__ import annotations


CRT_FRAGMENT_SHADER = """
#version 330
uniform sampler2D u_tex;
uniform vec2 u_resolution;
uniform vec2 u_texel;
uniform float u_time;

uniform float u_curvature;
uniform float u_chromatic_aberration;
uniform float u_scanline_strength;
uniform float u_scanline_density;
uniform float u_shadow_mask_strength;
uniform float u_vignette_strength;
uniform float u_bloom_strength;
uniform float u_glow_strength;
uniform float u_noise_amount;
uniform float u_jitter_amount;
uniform float u_glitch_amount;
uniform float u_ghost_amount;
uniform float u_contrast;
uniform float u_brightness;
uniform vec3 u_color_boost;
uniform int u_reseau_enabled;
uniform float u_reseau_spacing;
uniform float u_reseau_size;
uniform float u_reseau_thickness;
uniform float u_reseau_opacity;
uniform vec3 u_reseau_color;
uniform vec2 u_reseau_offset;
uniform float u_reseau_luma_cutoff;
uniform float u_reseau_luma_softness;

in vec2 v_uv;
out vec4 fragColor;

float rand(vec2 co) {
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

vec3 sample_tex(vec2 uv) {
    return texture(u_tex, uv).rgb;
}

void main() {
    vec2 uv = v_uv;
    vec2 centered = uv * 2.0 - 1.0;
    float r2 = dot(centered, centered);
    centered *= 1.0 + u_curvature * r2;
    uv = centered * 0.5 + 0.5;

    float jitter = (rand(vec2(u_time, uv.y * 137.0)) - 0.5) * u_jitter_amount;
    uv.x += jitter * u_texel.x * 8.0;

    float line = floor(uv.y * u_resolution.y);
    float glitch_gate = step(1.0 - u_glitch_amount, rand(vec2(line, u_time * 0.7)));
    float glitch = (rand(vec2(line, u_time * 1.7)) - 0.5) * 2.0;
    uv.x += glitch_gate * glitch * u_texel.x * 40.0 * u_glitch_amount;

    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    float ca = u_chromatic_aberration * u_texel.x;
    vec3 col = vec3(0.0);
    col.r = texture(u_tex, uv + vec2(ca, 0.0)).r;
    col.g = texture(u_tex, uv).g;
    col.b = texture(u_tex, uv - vec2(ca, 0.0)).b;

    vec3 ghost = texture(u_tex, uv + vec2(u_ghost_amount * 8.0 * u_texel.x, 0.0)).rgb;
    col = mix(col, ghost, u_ghost_amount);

    vec3 blur = (
        sample_tex(uv + vec2(1.0, 0.0) * u_texel) +
        sample_tex(uv + vec2(-1.0, 0.0) * u_texel) +
        sample_tex(uv + vec2(0.0, 1.0) * u_texel) +
        sample_tex(uv + vec2(0.0, -1.0) * u_texel) +
        sample_tex(uv + vec2(1.0, 1.0) * u_texel) +
        sample_tex(uv + vec2(-1.0, -1.0) * u_texel)
    ) / 6.0;
    vec3 glow = max(blur - vec3(0.6), vec3(0.0));
    col += blur * u_bloom_strength;
    col += glow * u_glow_strength;

    float scan = 0.5 + 0.5 * sin((uv.y * u_resolution.y) * 3.14159 * u_scanline_density);
    col *= mix(vec3(1.0), vec3(0.6 + 0.4 * scan), u_scanline_strength);

    float triad = mod(floor(uv.x * u_resolution.x), 3.0);
    vec3 mask = triad < 0.5 ? vec3(1.0, 0.7, 0.7)
        : (triad < 1.5 ? vec3(0.7, 1.0, 0.7) : vec3(0.7, 0.7, 1.0));
    col *= mix(vec3(1.0), mask, u_shadow_mask_strength);

    float vig = smoothstep(1.2, 0.2, dot(centered, centered));
    col *= mix(vec3(1.0), vec3(vig), u_vignette_strength);

    float noise = rand(uv * u_resolution + u_time) - 0.5;
    col += noise * u_noise_amount;

    col *= u_color_boost;
    col = (col - 0.5) * u_contrast + 0.5;
    col *= u_brightness;

    if (u_reseau_enabled == 1) {
        float spacing = max(1.0, u_reseau_spacing);
        vec2 p = uv * u_resolution + u_reseau_offset;
        vec2 cell = mod(p, spacing);
        vec2 d = abs(cell - vec2(0.5 * spacing));
        float hx = 1.0 - step(u_reseau_thickness, d.x);
        float hy = 1.0 - step(u_reseau_thickness, d.y);
        float vx = 1.0 - step(u_reseau_size, d.x);
        float vy = 1.0 - step(u_reseau_size, d.y);
        float mark = max(hx * vy, hy * vx);

        float lum = dot(col, vec3(0.299, 0.587, 0.114));
        float bg = 1.0 - smoothstep(u_reseau_luma_cutoff, u_reseau_luma_cutoff + u_reseau_luma_softness, lum);
        float mixv = mark * bg * u_reseau_opacity;
        col = mix(col, u_reseau_color, mixv);
    }

    col = clamp(col, 0.0, 1.0);
    fragColor = vec4(col, 1.0);
}
"""
