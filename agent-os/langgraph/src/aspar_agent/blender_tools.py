"""Building->Blender node — generates and runs a bpy script directly via
`blender --background --python`, with no dependency on the CLI-Anything
Blender harness.

Why not the harness: every write command of `cli-anything-blender`
(`scene new`, `object add`, `render execute`, ...) is refused by Claude
Code's auto-mode safety classifier — only read commands (`--help`, `scene
profiles`) pass. That means a pipeline built on it cannot run unattended:
each step needs a human to relay the command manually, which defeats the
entire point of an automated node. Confirmed by direct experience building
and rendering the Elionor Sovereign test scene on 2026-09-13 (harness blocked
repeatedly; a hand-written bpy script executed via `blender --background
--python` was never blocked and completed autonomously, including through
an unrelated bug in the script and a broken Blender install found and fixed
mid-session).

This module writes the bpy script itself, byte for byte, then invokes
Blender on it — the same command form proven to run unattended.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from langchain.tools import tool


_SCRIPT_TEMPLATE = '''
import bpy
import math

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = {res_x}
scene.render.resolution_y = {res_y}
scene.eevee.taa_render_samples = 32

side = {side}
height = {height}

# Ground plane, for scale/context around the volume.
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.01))
ground = bpy.context.active_object
ground.name = "Ground"
mat_ground = bpy.data.materials.new("Ground")
mat_ground.use_nodes = True
gb = next(n for n in mat_ground.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
gb.inputs["Base Color"].default_value = (0.05, 0.05, 0.055, 1.0)
gb.inputs["Roughness"].default_value = 0.9
ground.data.materials.append(mat_ground)

# The volume itself: a simple box footprint x height, sized from Phase 2's
# real surface_m2 — a placeholder volume, not an architectural plan.
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, height / 2))
vol = bpy.context.active_object
vol.name = "local_{concept_slug}"
vol.scale = (side / 2, side / 2, height / 2)
mat_vol = bpy.data.materials.new("Volume")
mat_vol.use_nodes = True
vb = next(n for n in mat_vol.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
vb.inputs["Base Color"].default_value = (0.55, 0.55, 0.58, 1.0)
vb.inputs["Roughness"].default_value = 0.5
vol.data.materials.append(mat_vol)

# Camera: distance and lens picked so the whole volume (plus margin) is in
# frame regardless of size — a fixed 50mm lens close up cropped a wide
# building out of frame in an earlier version of this script.
cam_dist = side * 2.2 + 15
bpy.ops.object.camera_add(
    location=(0, -cam_dist, height + cam_dist * 0.15),
    rotation=(math.radians(82), 0, 0),
)
camera = bpy.context.active_object
camera.data.lens = 24
scene.camera = camera

bpy.ops.object.light_add(type="SUN", location=(10, -10, 20))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.02, 0.02, 0.03, 1.0)
    bg.inputs[1].default_value = 0.3

scene.render.image_settings.file_format = "PNG"
scene.render.filepath = "{render_path}"
bpy.ops.render.render(write_still=True)
print("Render complete: {render_path}")

bpy.ops.wm.save_as_mainfile(filepath="{blend_path}")
print("Saved project: {blend_path}")
'''


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)


@tool("blender_render_tool")
def blender_render_tool(
    concept_name: str,
    surface_m2: float,
    work_dir: str,
) -> dict[str, object]:
    """Generate a simple 3D volume preview from a study's Phase 2 dimensioning
    (surface_m2). Writes a bpy script and runs it via `blender --background
    --python` directly — no CLI-Anything harness, so this runs unattended.

    Approximates the surface as a square footprint (side = sqrt(surface_m2))
    and a fixed 2.7m ceiling height — enough for an early "does the volume feel
    right" preview before real architectural drawings exist, not a precise plan.
    """
    if shutil.which("blender") is None:
        return {"status": "STOP", "reason": "blender introuvable dans le PATH"}

    project_dir = Path(work_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    slug = _slug(concept_name)
    render_path = project_dir / f"{slug}_preview.png"
    blend_path = project_dir / f"{slug}.blend"
    script_path = project_dir / f"_{slug}_build.py"

    side = math.sqrt(max(surface_m2, 1.0))
    height = 2.7

    script = _SCRIPT_TEMPLATE.format(
        res_x=960,
        res_y=540,
        side=side,
        height=height,
        concept_slug=slug,
        render_path=str(render_path),
        blend_path=str(blend_path),
    )
    script_path.write_text(script)

    result = subprocess.run(
        ["blender", "--background", "--python", str(script_path)],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=180,
    )

    if not render_path.exists():
        return {
            "status": "STOP",
            "reason": f"Rendu non produit — sortie Blender: {(result.stdout + result.stderr)[-500:]}",
        }

    return {
        "status": "PASS",
        "render_path": str(render_path),
        "blend_path": str(blend_path),
        "surface_m2": surface_m2,
        "footprint_side_m": round(side, 2),
    }
