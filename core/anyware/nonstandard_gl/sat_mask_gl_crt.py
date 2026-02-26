from __future__ import annotations

"""
Moderngl-based silhouette renderer with CRT/EL-style post-processing.

Integration note (to be extracted later):
- Create a pygame window with OPENGL|DOUBLEBUF flags.
- Create a moderngl context from that window.
- Instantiate SatMaskGLCRT(ctx, mesh_path, **params).
- Call update(dt) + render(width, height) each frame.
"""

import math
import random
import time
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pygame
import moderngl

try:
    from .sat_mask_gl_crt_effects import CRT_FRAGMENT_SHADER
except ImportError:
    from sat_mask_gl_crt_effects import CRT_FRAGMENT_SHADER


@dataclass
class MeshData:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, ...]]
    radius: float


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    n = math.sqrt(x * x + y * y + z * z)
    if n <= 1e-8:
        return (0.0, 0.0, 1.0)
    return (x / n, y / n, z / n)


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _axis_angle_matrix(axis: tuple[float, float, float], angle: float) -> list[list[float]]:
    ux, uy, uz = _normalize(axis)
    c = math.cos(angle)
    s = math.sin(angle)
    t = 1.0 - c
    return [
        [t * ux * ux + c, t * ux * uy - s * uz, t * ux * uz + s * uy, 0.0],
        [t * ux * uy + s * uz, t * uy * uy + c, t * uy * uz - s * ux, 0.0],
        [t * ux * uz - s * uy, t * uy * uz + s * ux, t * uz * uz + c, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _rotation_from_to(a: tuple[float, float, float], b: tuple[float, float, float]) -> list[list[float]]:
    na = _normalize(a)
    nb = _normalize(b)
    dot = max(-1.0, min(1.0, _dot(na, nb)))
    if dot > 0.999999:
        return _mat4_identity()
    if dot < -0.999999:
        ortho = (1.0, 0.0, 0.0) if abs(na[0]) < 0.9 else (0.0, 1.0, 0.0)
        axis = _cross(na, ortho)
        return _axis_angle_matrix(axis, math.pi)
    axis = _cross(na, nb)
    angle = math.acos(dot)
    return _axis_angle_matrix(axis, angle)


def _mat4_identity() -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _mat4_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    out = [[0.0, 0.0, 0.0, 0.0] for _ in range(4)]
    for r in range(4):
        for c in range(4):
            out[r][c] = (
                a[r][0] * b[0][c]
                + a[r][1] * b[1][c]
                + a[r][2] * b[2][c]
                + a[r][3] * b[3][c]
            )
    return out


def _mat4_scale(s: float) -> list[list[float]]:
    return [
        [s, 0.0, 0.0, 0.0],
        [0.0, s, 0.0, 0.0],
        [0.0, 0.0, s, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _mat4_perspective(fov_deg: float, aspect: float, z_near: float, z_far: float) -> list[list[float]]:
    f = 1.0 / math.tan(math.radians(fov_deg) * 0.5)
    return [
        [f / aspect, 0.0, 0.0, 0.0],
        [0.0, f, 0.0, 0.0],
        [0.0, 0.0, (z_far + z_near) / (z_near - z_far), (2.0 * z_far * z_near) / (z_near - z_far)],
        [0.0, 0.0, -1.0, 0.0],
    ]


def _mat4_look_at(eye: tuple[float, float, float], target: tuple[float, float, float], up: tuple[float, float, float]) -> list[list[float]]:
    fx, fy, fz = _normalize((target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]))
    ux, uy, uz = _normalize(up)
    sx, sy, sz = _normalize(_cross((fx, fy, fz), (ux, uy, uz)))
    ux, uy, uz = _cross((sx, sy, sz), (fx, fy, fz))

    return [
        [sx, sy, sz, -_dot((sx, sy, sz), eye)],
        [ux, uy, uz, -_dot((ux, uy, uz), eye)],
        [-fx, -fy, -fz, _dot((fx, fy, fz), eye)],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _flatten_mat4(m: list[list[float]]) -> bytes:
    return array("f", [m[r][c] for c in range(4) for r in range(4)]).tobytes()


def _as_color(value: Iterable[float | int]) -> tuple[float, float, float]:
    vals = list(value)
    if not vals:
        return (1.0, 1.0, 1.0)
    if max(vals) > 1.0:
        return (vals[0] / 255.0, vals[1] / 255.0, vals[2] / 255.0)
    return (float(vals[0]), float(vals[1]), float(vals[2]))


def _as_vec3(value: Iterable[float | int], default: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> tuple[float, float, float]:
    vals = list(value)
    if len(vals) < 3:
        return default
    return (float(vals[0]), float(vals[1]), float(vals[2]))


def _load_obj(path: Path) -> MeshData:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line or line.startswith("#"):
                continue
            if line.startswith("v "):
                parts = line.strip().split()
                if len(parts) >= 4:
                    vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif line.startswith("f "):
                parts = line.strip().split()[1:]
                idxs: list[int] = []
                for part in parts:
                    if not part:
                        continue
                    i_str = part.split("/")[0]
                    if not i_str:
                        continue
                    idx = int(i_str)
                    if idx < 0:
                        idx = len(vertices) + idx + 1
                    idxs.append(idx - 1)
                if len(idxs) >= 3:
                    faces.append(tuple(idxs))
    radius = 1.0
    if vertices:
        radius = max(math.sqrt(x * x + y * y + z * z) for x, y, z in vertices)
    return MeshData(vertices, faces, radius)


VERTEX_SHADER = """
#version 330
in vec3 in_pos;

uniform mat4 u_mvp;
uniform float u_depth_bias;

void main() {
    vec4 pos = u_mvp * vec4(in_pos, 1.0);
    pos.z += u_depth_bias * pos.w;
    gl_Position = pos;
}
"""


FRAGMENT_SHADER = """
#version 330
uniform vec2 u_mask_n;
uniform float u_mask_offset;
uniform vec2 u_origin_px;
uniform vec3 u_dark_color;
uniform vec3 u_light_color;
uniform sampler2D u_img_tex;
uniform vec2 u_img_size;
uniform vec2 u_img_scale;
uniform vec2 u_img_offset_px;
uniform float u_img_alpha_threshold;
uniform int u_img_enabled;
uniform float u_layer_value;
uniform int u_bg_mode;
uniform float u_pixel_scale;

out vec4 fragColor;

void main() {
    // Convert to center-origin, Y-down coordinates
    vec2 frag_px = gl_FragCoord.xy * u_pixel_scale;
    vec2 p = vec2(frag_px.x - u_origin_px.x, u_origin_px.y - frag_px.y);
    float side = dot(u_mask_n, p) - u_mask_offset;
    float diag = (side >= 0.0) ? -1.0 : 1.0;
    float img = 1.0;
    bool img_on = false;
    if (u_img_enabled == 1) {
        vec2 size = u_img_size * u_img_scale;
        if (size.x > 0.5 && size.y > 0.5) {
            vec2 local = p - u_img_offset_px;
            vec2 uv = (local + 0.5 * size) / size;
            uv.y = 1.0 - uv.y;
            if (uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0) {
                float a = texture(u_img_tex, uv).a;
                if (a > u_img_alpha_threshold) {
                    img = -1.0;
                    img_on = true;
                }
            }
        }
    }
    if (u_bg_mode == 1) {
        if (!(img_on && diag < 0.0)) {
            fragColor = vec4(u_dark_color, 1.0);
            return;
        }
    }
    float prod = u_layer_value * diag * img;
    vec3 out_color = (prod >= 0.0) ? u_light_color : u_dark_color;
    fragColor = vec4(out_color, 1.0);
}
"""


BLIT_VERTEX_SHADER = """
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 v_uv;
void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""


BLIT_FRAGMENT_SHADER = """
#version 330
uniform sampler2D u_tex;
in vec2 v_uv;
out vec4 fragColor;
void main() {
    fragColor = texture(u_tex, v_uv);
}
"""






class SatMaskGLCRT:
    def __init__(
        self,
        ctx: moderngl.Context,
        mesh_path: Path,
        *,
        rotation_axis: tuple[float, float, float] = (0.0, 0.0, 1.0),
        rotation_axis_dir: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation_speed: float = 0.6,
        cam_dist: float = 3.0,
        fov_deg: float = 35.0,
        z_near: float = 0.1,
        z_far: float = 100.0,
        model_scale: float = 1.0,
        model_center: tuple[float, float, float] = (0.0, 0.0, 0.0),
        mask_angle_deg: float = 45.0,
        mask_offset_px: float = 0.0,
        origin_offset_px: tuple[float, float] = (0.0, 0.0),
        mask_image_path: Path | str | None = None,
        mask_image_scale: float | tuple[float, float] = 1.0,
        mask_image_offset_px: tuple[float, float] = (0.0, 0.0),
        mask_image_alpha_threshold: float = 0.5,
        mask_image_enabled: bool = True,
        dark_color: Iterable[float | int] = (10, 10, 10),
        light_color: Iterable[float | int] = (255, 255, 255),
        bg_color: Iterable[float | int] = (10, 10, 10),
        pixel_scale: int = 1,
        line_width: float = 1.0,
        crt_enabled: bool = True,
        crt_curvature: float = 0.08,
        crt_chromatic_aberration: float = 1.0,
        crt_scanline_strength: float = 0.25,
        crt_scanline_density: float = 1.0,
        crt_shadow_mask_strength: float = 0.25,
        crt_vignette_strength: float = 0.35,
        crt_bloom_strength: float = 0.18,
        crt_glow_strength: float = 0.25,
        crt_noise_amount: float = 0.02,
        crt_jitter_amount: float = 0.35,
        crt_glitch_amount: float = 0.35,
        crt_ghost_amount: float = 0.12,
        crt_contrast: float = 1.05,
        crt_brightness: float = 1.02,
        crt_color_boost: Iterable[float | int] = (1.04, 1.0, 0.97),
        reseau_enabled: bool = True,
        reseau_spacing_px: float = 80.0,
        reseau_size_px: float = 6.0,
        reseau_thickness_px: float = 1.0,
        reseau_opacity: float = 0.7,
        reseau_color: Iterable[float | int] = (0, 0, 0),
        reseau_offset_px: tuple[float, float] = (0.0, 0.0),
        reseau_luma_cutoff: float = 0.35,
        reseau_luma_softness: float = 0.12,
        startup_black_seconds: float = 2.0,
        startup_flicker_seconds: float = 2.5,
        startup_flicker_intensity: float = 0.65,
        startup_flicker_speed: float = 16.0,
        startup_flicker_noise_boost: float = 2.5,
    ) -> None:
        self.ctx = ctx
        self.mesh_path = mesh_path
        self.mesh = _load_obj(mesh_path)

        self.rotation_axis = rotation_axis
        self.rotation_axis_dir = rotation_axis_dir
        self.rotation_speed = float(rotation_speed)
        self.rotation_angle = 0.0

        self.cam_dist = float(cam_dist)
        self.fov_deg = float(fov_deg)
        self.z_near = float(z_near)
        self.z_far = float(z_far)
        self.model_scale = float(model_scale)
        self.model_center = model_center

        self.mask_angle_deg = float(mask_angle_deg)
        self.mask_offset_px = float(mask_offset_px)
        self.origin_offset_px = origin_offset_px
        self.mask_image_path = Path(mask_image_path) if mask_image_path else None
        if isinstance(mask_image_scale, (list, tuple)):
            self.mask_image_scale = (float(mask_image_scale[0]), float(mask_image_scale[1]))
        else:
            v = float(mask_image_scale)
            self.mask_image_scale = (v, v)
        if isinstance(mask_image_offset_px, (list, tuple)) and len(mask_image_offset_px) >= 2:
            self.mask_image_offset_px = (float(mask_image_offset_px[0]), float(mask_image_offset_px[1]))
        else:
            self.mask_image_offset_px = (float(mask_image_offset_px), 0.0)
        self.mask_image_alpha_threshold = float(mask_image_alpha_threshold)
        self.mask_image_enabled = bool(mask_image_enabled)

        self.bg_color = _as_color(bg_color)
        self.pixel_scale = max(1, int(pixel_scale))
        self.line_width = max(1.0, float(line_width))
        self.dark_color = _as_color(dark_color)
        self.light_color = _as_color(light_color)

        self.crt_enabled = bool(crt_enabled)
        self.crt_curvature = float(crt_curvature)
        self.crt_chromatic_aberration = float(crt_chromatic_aberration)
        self.crt_scanline_strength = float(crt_scanline_strength)
        self.crt_scanline_density = float(crt_scanline_density)
        self.crt_shadow_mask_strength = float(crt_shadow_mask_strength)
        self.crt_vignette_strength = float(crt_vignette_strength)
        self.crt_bloom_strength = float(crt_bloom_strength)
        self.crt_glow_strength = float(crt_glow_strength)
        self.crt_noise_amount = float(crt_noise_amount)
        self.crt_jitter_amount = float(crt_jitter_amount)
        self.crt_glitch_amount = float(crt_glitch_amount)
        self.crt_ghost_amount = float(crt_ghost_amount)
        self.crt_contrast = float(crt_contrast)
        self.crt_brightness = float(crt_brightness)
        self.crt_color_boost = _as_vec3(crt_color_boost)
        self.reseau_enabled = bool(reseau_enabled)
        self.reseau_spacing_px = float(reseau_spacing_px)
        self.reseau_size_px = float(reseau_size_px)
        self.reseau_thickness_px = float(reseau_thickness_px)
        self.reseau_opacity = float(reseau_opacity)
        self.reseau_color = _as_color(reseau_color)
        if isinstance(reseau_offset_px, (list, tuple)) and len(reseau_offset_px) >= 2:
            self.reseau_offset_px = (float(reseau_offset_px[0]), float(reseau_offset_px[1]))
        else:
            self.reseau_offset_px = (float(reseau_offset_px), 0.0)
        self.reseau_luma_cutoff = float(reseau_luma_cutoff)
        self.reseau_luma_softness = float(reseau_luma_softness)
        self.startup_black_seconds = float(startup_black_seconds)
        self.startup_flicker_seconds = float(startup_flicker_seconds)
        self.startup_flicker_intensity = float(startup_flicker_intensity)
        self.startup_flicker_speed = float(startup_flicker_speed)
        self.startup_flicker_noise_boost = float(startup_flicker_noise_boost)
        self._time = 0.0
        self._startup_brightness = 1.0

        self.prog = self.ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
        self.blit_prog = self.ctx.program(vertex_shader=BLIT_VERTEX_SHADER, fragment_shader=BLIT_FRAGMENT_SHADER)
        self.crt_prog = self.ctx.program(vertex_shader=BLIT_VERTEX_SHADER, fragment_shader=CRT_FRAGMENT_SHADER)

        self._init_buffers()
        self._init_bg_buffers()
        self._init_mask_texture(self.mask_image_path)
        self._init_post_buffers()

        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)

    def _init_buffers(self) -> None:
        if not self.mesh.vertices or not self.mesh.faces:
            raise ValueError("Empty mesh")

        cx, cy, cz = self.model_center
        self.mesh_radius = 1.0
        packed = array("f")
        max_r = 0.0
        for x, y, z in self.mesh.vertices:
            dx = x - cx
            dy = y - cy
            dz = z - cz
            packed.extend((dx, dy, dz))
            r = math.sqrt(dx * dx + dy * dy + dz * dz)
            if r > max_r:
                max_r = r
        self.mesh_radius = max(1e-8, max_r)

        tri_indices = array("I")
        for face in self.mesh.faces:
            if len(face) < 3:
                continue
            v0 = face[0]
            for i in range(1, len(face) - 1):
                tri_indices.extend((v0, face[i], face[i + 1]))

        edge_set: set[tuple[int, int]] = set()
        for face in self.mesh.faces:
            count = len(face)
            for i in range(count):
                a = face[i]
                b = face[(i + 1) % count]
                key = (a, b) if a < b else (b, a)
                edge_set.add(key)

        line_indices = array("I")
        for a, b in edge_set:
            line_indices.extend((a, b))

        self.vbo = self.ctx.buffer(packed.tobytes())
        self.ibo_tri = self.ctx.buffer(tri_indices.tobytes())
        self.ibo_line = self.ctx.buffer(line_indices.tobytes())

        self.vao_tri = self.ctx.vertex_array(self.prog, [(self.vbo, "3f", "in_pos")], self.ibo_tri)
        self.vao_line = self.ctx.vertex_array(self.prog, [(self.vbo, "3f", "in_pos")], self.ibo_line)

    def _init_bg_buffers(self) -> None:
        quad = array("f", [-1.0, -1.0, 0.0, 3.0, -1.0, 0.0, -1.0, 3.0, 0.0])
        self.bg_vbo = self.ctx.buffer(quad.tobytes())
        self.bg_vao = self.ctx.vertex_array(self.prog, [(self.bg_vbo, "3f", "in_pos")])

    def _init_post_buffers(self) -> None:
        verts = array(
            "f",
            [
                -1.0, -1.0, 0.0, 0.0,
                1.0, -1.0, 1.0, 0.0,
                1.0, 1.0, 1.0, 1.0,
                -1.0, -1.0, 0.0, 0.0,
                1.0, 1.0, 1.0, 1.0,
                -1.0, 1.0, 0.0, 1.0,
            ],
        )
        self.post_vbo = self.ctx.buffer(verts.tobytes())
        self.post_vao = self.ctx.vertex_array(
            self.blit_prog,
            [(self.post_vbo, "2f 2f", "in_pos", "in_uv")],
        )
        self.crt_vao = self.ctx.vertex_array(
            self.crt_prog,
            [(self.post_vbo, "2f 2f", "in_pos", "in_uv")],
        )
        self.scene_fbo = None
        self.scene_tex = None
        self.scene_size = (0, 0)

    def _init_mask_texture(self, path: Path | None) -> None:
        self.mask_tex = None
        self.mask_size = (1.0, 1.0)
        if path is None:
            self.mask_image_enabled = False
            return
        if not path.exists():
            self.mask_image_enabled = False
            return
        try:
            import pygame
        except Exception:
            self.mask_image_enabled = False
            return
        surf = pygame.image.load(str(path)).convert_alpha()
        w, h = surf.get_size()
        data = pygame.image.tostring(surf, "RGBA", False)
        tex = self.ctx.texture((w, h), 4, data)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        tex.repeat_x = False
        tex.repeat_y = False
        self.mask_tex = tex
        self.mask_size = (float(w), float(h))

    def apply_params(self, params: dict) -> None:
        if not params:
            return
        if "rotation_axis" in params:
            self.rotation_axis = tuple(params["rotation_axis"])
        if "rotation_axis_dir" in params:
            self.rotation_axis_dir = tuple(params["rotation_axis_dir"])
        if "rotation_speed" in params:
            self.rotation_speed = float(params["rotation_speed"])
        if "cam_dist" in params:
            self.cam_dist = float(params["cam_dist"])
        if "fov_deg" in params:
            self.fov_deg = float(params["fov_deg"])
        if "model_scale" in params:
            self.model_scale = float(params["model_scale"])
        if "mask_angle_deg" in params:
            self.mask_angle_deg = float(params["mask_angle_deg"])
        if "mask_offset_px" in params:
            self.mask_offset_px = float(params["mask_offset_px"])
        if "origin_offset_px" in params:
            self.origin_offset_px = tuple(params["origin_offset_px"])
        if "mask_image_scale" in params:
            value = params["mask_image_scale"]
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                self.mask_image_scale = (float(value[0]), float(value[1]))
            else:
                v = float(value)
                self.mask_image_scale = (v, v)
        if "mask_image_offset_px" in params:
            value = params["mask_image_offset_px"]
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                self.mask_image_offset_px = (float(value[0]), float(value[1]))
            else:
                self.mask_image_offset_px = (float(value), 0.0)
        if "mask_image_alpha_threshold" in params:
            self.mask_image_alpha_threshold = float(params["mask_image_alpha_threshold"])
        if "mask_image_enabled" in params:
            self.mask_image_enabled = bool(params["mask_image_enabled"])
        if "mask_image_path" in params:
            path = params["mask_image_path"]
            self.mask_image_path = Path(path) if path else None
            self._init_mask_texture(self.mask_image_path)
        if "dark_color" in params:
            self.dark_color = _as_color(params["dark_color"])
        if "light_color" in params:
            self.light_color = _as_color(params["light_color"])
        if "bg_color" in params:
            self.bg_color = _as_color(params["bg_color"])
        if "pixel_scale" in params:
            self.pixel_scale = max(1, int(params["pixel_scale"]))
        if "line_width" in params:
            self.line_width = max(1.0, float(params["line_width"]))
        if "crt_enabled" in params:
            self.crt_enabled = bool(params["crt_enabled"])
        if "crt_curvature" in params:
            self.crt_curvature = float(params["crt_curvature"])
        if "crt_chromatic_aberration" in params:
            self.crt_chromatic_aberration = float(params["crt_chromatic_aberration"])
        if "crt_scanline_strength" in params:
            self.crt_scanline_strength = float(params["crt_scanline_strength"])
        if "crt_scanline_density" in params:
            self.crt_scanline_density = float(params["crt_scanline_density"])
        if "crt_shadow_mask_strength" in params:
            self.crt_shadow_mask_strength = float(params["crt_shadow_mask_strength"])
        if "crt_vignette_strength" in params:
            self.crt_vignette_strength = float(params["crt_vignette_strength"])
        if "crt_bloom_strength" in params:
            self.crt_bloom_strength = float(params["crt_bloom_strength"])
        if "crt_glow_strength" in params:
            self.crt_glow_strength = float(params["crt_glow_strength"])
        if "crt_noise_amount" in params:
            self.crt_noise_amount = float(params["crt_noise_amount"])
        if "crt_jitter_amount" in params:
            self.crt_jitter_amount = float(params["crt_jitter_amount"])
        if "crt_glitch_amount" in params:
            self.crt_glitch_amount = float(params["crt_glitch_amount"])
        if "crt_ghost_amount" in params:
            self.crt_ghost_amount = float(params["crt_ghost_amount"])
        if "crt_contrast" in params:
            self.crt_contrast = float(params["crt_contrast"])
        if "crt_brightness" in params:
            self.crt_brightness = float(params["crt_brightness"])
        if "crt_color_boost" in params:
            self.crt_color_boost = _as_vec3(params["crt_color_boost"])
        if "reseau_enabled" in params:
            self.reseau_enabled = bool(params["reseau_enabled"])
        if "reseau_spacing_px" in params:
            self.reseau_spacing_px = float(params["reseau_spacing_px"])
        if "reseau_size_px" in params:
            self.reseau_size_px = float(params["reseau_size_px"])
        if "reseau_thickness_px" in params:
            self.reseau_thickness_px = float(params["reseau_thickness_px"])
        if "reseau_opacity" in params:
            self.reseau_opacity = float(params["reseau_opacity"])
        if "reseau_color" in params:
            self.reseau_color = _as_color(params["reseau_color"])
        if "reseau_offset_px" in params:
            value = params["reseau_offset_px"]
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                self.reseau_offset_px = (float(value[0]), float(value[1]))
            else:
                self.reseau_offset_px = (float(value), 0.0)
        if "reseau_luma_cutoff" in params:
            self.reseau_luma_cutoff = float(params["reseau_luma_cutoff"])
        if "reseau_luma_softness" in params:
            self.reseau_luma_softness = float(params["reseau_luma_softness"])
        if "startup_black_seconds" in params:
            self.startup_black_seconds = float(params["startup_black_seconds"])
        if "startup_flicker_seconds" in params:
            self.startup_flicker_seconds = float(params["startup_flicker_seconds"])
        if "startup_flicker_intensity" in params:
            self.startup_flicker_intensity = float(params["startup_flicker_intensity"])
        if "startup_flicker_speed" in params:
            self.startup_flicker_speed = float(params["startup_flicker_speed"])
        if "startup_flicker_noise_boost" in params:
            self.startup_flicker_noise_boost = float(params["startup_flicker_noise_boost"])

    def update(self, dt: float) -> None:
        self.rotation_angle += self.rotation_speed * dt
        self._time += float(dt)

    def _set_mask_uniforms(self, prog, width: int, height: int) -> None:
        angle = math.radians(self.mask_angle_deg)
        mask_n = (-math.sin(angle), math.cos(angle))
        origin = (width * 0.5 + self.origin_offset_px[0], height * 0.5 + self.origin_offset_px[1])

        prog["u_mask_n"].value = mask_n
        prog["u_mask_offset"].value = float(self.mask_offset_px)
        prog["u_origin_px"].value = origin

        if "u_dark_color" in prog:
            prog["u_dark_color"].value = self.dark_color
        if "u_light_color" in prog:
            prog["u_light_color"].value = self.light_color

        prog["u_img_size"].value = self.mask_size
        prog["u_img_scale"].value = self.mask_image_scale
        prog["u_img_offset_px"].value = self.mask_image_offset_px
        prog["u_img_alpha_threshold"].value = float(self.mask_image_alpha_threshold)
        enabled = 1 if (self.mask_image_enabled and self.mask_tex is not None) else 0
        prog["u_img_enabled"].value = enabled
        if "u_pixel_scale" in prog:
            prog["u_pixel_scale"].value = float(self.pixel_scale)
        if self.mask_tex is not None:
            self.mask_tex.use(location=0)
            prog["u_img_tex"].value = 0

    def _set_common_uniforms(self, width: int, height: int) -> None:
        aspect = max(1e-6, width / max(1.0, float(height)))
        proj = _mat4_perspective(self.fov_deg, aspect, self.z_near, self.z_far)

        base_axis = _normalize(self.rotation_axis)
        axis_dir = self.rotation_axis_dir
        if _dot(axis_dir, axis_dir) <= 1e-8:
            axis_dir = base_axis
        align = _rotation_from_to(base_axis, axis_dir)
        spin = _axis_angle_matrix(base_axis, self.rotation_angle)
        scale = self.model_scale / self.mesh_radius
        scale_m = _mat4_scale(scale)
        model = _mat4_mul(align, _mat4_mul(spin, scale_m))

        view = _mat4_look_at((0.0, 0.0, self.cam_dist), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        mvp = _mat4_mul(proj, _mat4_mul(view, model))

        self.prog["u_mvp"].write(_flatten_mat4(mvp))
        self._set_mask_uniforms(self.prog, width, height)

    def _set_crt_uniforms(self, width: int, height: int, render_w: int, render_h: int) -> None:
        prog = self.crt_prog
        prog["u_tex"].value = 0
        prog["u_resolution"].value = (float(width), float(height))
        prog["u_texel"].value = (1.0 / max(1.0, float(render_w)), 1.0 / max(1.0, float(render_h)))
        prog["u_time"].value = float(self._time)

        prog["u_curvature"].value = float(self.crt_curvature)
        prog["u_chromatic_aberration"].value = float(self.crt_chromatic_aberration)
        prog["u_scanline_strength"].value = float(self.crt_scanline_strength)
        prog["u_scanline_density"].value = float(self.crt_scanline_density)
        prog["u_shadow_mask_strength"].value = float(self.crt_shadow_mask_strength)
        prog["u_vignette_strength"].value = float(self.crt_vignette_strength)
        prog["u_bloom_strength"].value = float(self.crt_bloom_strength)
        prog["u_glow_strength"].value = float(self.crt_glow_strength)
        noise_scale = 1.0 + (1.0 - self._startup_brightness) * self.startup_flicker_noise_boost
        prog["u_noise_amount"].value = float(self.crt_noise_amount) * noise_scale
        prog["u_jitter_amount"].value = float(self.crt_jitter_amount)
        prog["u_glitch_amount"].value = float(self.crt_glitch_amount)
        prog["u_ghost_amount"].value = float(self.crt_ghost_amount)
        prog["u_contrast"].value = float(self.crt_contrast)
        prog["u_brightness"].value = float(self.crt_brightness) * self._startup_brightness
        prog["u_color_boost"].value = self.crt_color_boost
        prog["u_reseau_enabled"].value = 1 if self.reseau_enabled else 0
        prog["u_reseau_spacing"].value = float(self.reseau_spacing_px)
        prog["u_reseau_size"].value = float(self.reseau_size_px)
        prog["u_reseau_thickness"].value = float(self.reseau_thickness_px)
        prog["u_reseau_opacity"].value = float(self.reseau_opacity)
        prog["u_reseau_color"].value = self.reseau_color
        prog["u_reseau_offset"].value = self.reseau_offset_px
        prog["u_reseau_luma_cutoff"].value = float(self.reseau_luma_cutoff)
        prog["u_reseau_luma_softness"].value = float(self.reseau_luma_softness)

    def _ensure_scene_buffer(self, width: int, height: int) -> tuple[int, int]:
        scale = self.pixel_scale if self.pixel_scale > 1 else 1
        target_w = max(1, int(width / scale))
        target_h = max(1, int(height / scale))
        if self.scene_tex is None or self.scene_size != (target_w, target_h):
            self.scene_tex = self.ctx.texture((target_w, target_h), 4)
            self.scene_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self.scene_fbo = self.ctx.framebuffer(color_attachments=[self.scene_tex])
            self.scene_size = (target_w, target_h)
        return target_w, target_h

    def _startup_brightness_scale(self) -> float:
        t = self._time
        if t < self.startup_black_seconds:
            return 0.0
        t -= self.startup_black_seconds
        if t < self.startup_flicker_seconds:
            phase = t / max(1e-3, self.startup_flicker_seconds)
            ramp = phase * phase * (3.0 - 2.0 * phase)
            wave = abs(math.sin(t * self.startup_flicker_speed))
            noise = random.random()
            flicker = 0.15 + 0.85 * (0.5 * wave + 0.5 * noise)
            intensity = max(0.0, min(1.0, self.startup_flicker_intensity * (1.0 - 0.2 * phase)))
            return max(0.0, min(1.0, ramp * (1.0 - intensity + intensity * flicker)))
        return 1.0

    def render(self, width: int, height: int) -> None:
        self._startup_brightness = self._startup_brightness_scale()
        if self._startup_brightness <= 0.0:
            self.ctx.screen.use()
            self.ctx.viewport = (0, 0, width, height)
            self.ctx.disable(moderngl.DEPTH_TEST)
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            return
        render_to_texture = self.crt_enabled or self.pixel_scale > 1
        render_w, render_h = width, height
        if render_to_texture:
            render_w, render_h = self._ensure_scene_buffer(width, height)
            if self.scene_fbo is not None:
                self.scene_fbo.use()
                self.ctx.viewport = (0, 0, render_w, render_h)
        else:
            self.ctx.screen.use()
            self.ctx.viewport = (0, 0, width, height)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.clear(self.bg_color[0], self.bg_color[1], self.bg_color[2], 1.0)

        if self.mask_image_enabled and self.mask_tex is not None:
            self.ctx.disable(moderngl.DEPTH_TEST)
            self.prog["u_mvp"].write(_flatten_mat4(_mat4_identity()))
            self._set_mask_uniforms(self.prog, width, height)
            self.prog["u_depth_bias"].value = 0.0
            self.prog["u_layer_value"].value = 1.0
            self.prog["u_bg_mode"].value = 1
            self.bg_vao.render(moderngl.TRIANGLES)
            self.ctx.enable(moderngl.DEPTH_TEST)

        self._set_common_uniforms(width, height)

        self.prog["u_depth_bias"].value = 0.0
        self.prog["u_layer_value"].value = 1.0
        self.prog["u_bg_mode"].value = 0
        self.vao_tri.render(moderngl.TRIANGLES)

        self.ctx.line_width = self.line_width
        self.prog["u_depth_bias"].value = -1.0e-4
        self.prog["u_layer_value"].value = -1.0
        self.prog["u_bg_mode"].value = 0
        self.vao_line.render(moderngl.LINES)

        if render_to_texture and self.scene_tex is not None:
            self.ctx.screen.use()
            self.ctx.viewport = (0, 0, width, height)
            self.scene_tex.use(location=0)
            self.ctx.disable(moderngl.DEPTH_TEST)
            if self.crt_enabled:
                self._set_crt_uniforms(width, height, render_w, render_h)
                self.crt_vao.render(moderngl.TRIANGLES)
            else:
                self.blit_prog["u_tex"].value = 0
                self.post_vao.render(moderngl.TRIANGLES)


REPO_ROOT = Path(__file__).resolve().parents[3]
MESH_PATH = REPO_ROOT / "assets" / "meshes" / "sat.obj"
MASK_PATH = REPO_ROOT / "assets" / "images" / "mask_v3.png"

APP_CONFIG = {
    "window_size": (1280, 720),
    "fullscreen": True,
    "caption": "Sat Mask GL CRT",
    "target_fps": 60,
}

PARAMS = {
    "rotation_axis": (0.0, 1.0, 0.0),
    "rotation_axis_dir": (2.0, 3.0, 1.0),
    "rotation_speed": 0.3,
    "cam_dist": 5.0,
    "fov_deg": 40.0,
    "model_scale": 2.0,
    "mask_angle_deg": 45.0,
    "mask_offset_px": 0.0,
    "origin_offset_px": (0.0, 0.0),
    "mask_image_path": str(MASK_PATH),
    "mask_image_scale": 0.4,
    "mask_image_offset_px": (-80, 40),
    "mask_image_alpha_threshold": 0.1,
    "mask_image_enabled": True,
    "dark_color": (210, 200, 190), # dark and light can be reversed to alternate dark/solarized theme
    "light_color": (121, 162, 10),
    "bg_color": (210, 200, 190),
    "pixel_scale": 1,
    "line_width": 10,
    # CRT / EL display post-process parameters
    "crt_enabled": True,
    "crt_curvature": 0.03,
    "crt_chromatic_aberration": 0.5,
    "crt_scanline_strength": 0.20,
    "crt_scanline_density": 1.0,
    "crt_shadow_mask_strength": 0.1,
    "crt_vignette_strength": 0.15,
    "crt_bloom_strength": 0.28,
    "crt_glow_strength": 0.35,
    "crt_noise_amount": 0.01,
    "crt_jitter_amount": 0.04,
    "crt_glitch_amount": 0.04,
    "crt_ghost_amount": 0.12,
    "crt_contrast": 1.01,
    "crt_brightness": 1.01,
    "crt_color_boost": (1.02, 1.00, 0.97),
    # Reseau (fiducial) marks
    "reseau_enabled": True,
    "reseau_spacing_px": 80.0,
    "reseau_size_px": 8.0,
    "reseau_thickness_px": 1.0,
    "reseau_opacity": 0.7,
    "reseau_color": (100, 70, 30),
    "reseau_offset_px": (0.0, 0.0),
    "reseau_luma_cutoff": 0.35,
    "reseau_luma_softness": 0.32,
    # Startup boot / flicker
    "startup_black_seconds": 2.0,
    "startup_flicker_seconds": 5.0,
    "startup_flicker_intensity": 0.3,
    "startup_flicker_speed": 12.0,
    "startup_flicker_noise_boost": 3.0,
}


def main() -> None:
    pygame.init()

    window_w, window_h = APP_CONFIG["window_size"]
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, 1)
    flags = pygame.OPENGL | pygame.DOUBLEBUF
    if APP_CONFIG["fullscreen"]:
        flags |= pygame.FULLSCREEN
    pygame.display.set_mode((window_w, window_h), flags)
    pygame.display.set_caption(APP_CONFIG["caption"])

    ctx = moderngl.create_context(require=330)
    sat = SatMaskGLCRT(ctx, MESH_PATH, **PARAMS)

    clock = pygame.time.Clock()
    last_time = time.time()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        now = time.time()
        dt = now - last_time
        last_time = now

        sat.update(dt)
        sat.render(window_w, window_h)

        pygame.display.flip()
        clock.tick(APP_CONFIG["target_fps"])

    pygame.quit()


if __name__ == "__main__":
    main()
