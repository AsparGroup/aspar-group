"""Building→Blender node — automates the SOP proven manually on 2026-09-13:
scene new -> object add -> camera add -> light add -> render (blender --background).

Each step is one subprocess call to the CLI-Anything Blender harness
(`cli-anything-blender`), chained in sequence — a single automated SOP
instead of the same commands run one at a time by hand. The render step
needs a separate `blender --background --python` call because the harness's
`render execute` only generates the bpy script, it does not invoke Blender
itself (confirmed manually before writing this).
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from langchain.tools import tool


def _run(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout


@tool("blender_render_tool")
def blender_render_tool(
    concept_name: str,
    surface_m2: float,
    work_dir: str,
) -> dict[str, object]:
    """Generate a simple 3D volume preview from a study's Phase 2 dimensioning
    (surface_m2), automating the SOP: scene -> object -> camera -> light -> render.

    Approximates the surface as a square footprint (side = sqrt(surface_m2))
    and a fixed 2.7m ceiling height — enough for an early "does the volume feel
    right" preview before real architectural drawings exist, not a precise plan.
    """
    if shutil.which("cli-anything-blender") is None:
        return {"status": "STOP", "reason": "cli-anything-blender introuvable dans le PATH"}
    if shutil.which("blender") is None:
        return {"status": "STOP", "reason": "blender introuvable dans le PATH"}

    project_dir = Path(work_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    project_path = project_dir / f"{concept_name}.json"
    render_path = project_dir / f"{concept_name}_preview.png"
    script_path = project_dir / "_render_script.py"

    side = math.sqrt(max(surface_m2, 1.0))
    height = 2.7

    _run(
        [
            "cli-anything-blender", "scene", "new",
            "--name", concept_name, "--profile", "preview",
            "-o", str(project_path),
        ],
        cwd=project_dir,
    )
    _run(
        [
            "cli-anything-blender", "--project", str(project_path),
            "object", "add", "cube",
            "--name", f"local_{concept_name}",
            "-s", f"{side / 2},{side / 2},{height / 2}",
            "-l", f"0,0,{height / 2}",
        ],
        cwd=project_dir,
    )
    _run(
        [
            "cli-anything-blender", "--project", str(project_path),
            "camera", "add", "--name", "cam1",
            "-l", f"{side * 1.5},{-side * 1.5},{side}",
            "-r", "60,0,45",
        ],
        cwd=project_dir,
    )
    _run(
        [
            "cli-anything-blender", "--project", str(project_path),
            "light", "add", "sun", "--name", "sun1",
        ],
        cwd=project_dir,
    )
    _run(
        [
            "cli-anything-blender", "--project", str(project_path),
            "render", "execute", str(render_path),
        ],
        cwd=project_dir,
    )

    if not script_path.exists():
        return {"status": "STOP", "reason": "Script de rendu non généré par le harness"}

    render_output = _run(
        ["blender", "--background", "--python", str(script_path)],
        cwd=project_dir,
    )

    if not render_path.exists():
        return {
            "status": "STOP",
            "reason": f"Rendu non produit — sortie Blender: {render_output[-500:]}",
        }

    return {
        "status": "PASS",
        "render_path": str(render_path),
        "surface_m2": surface_m2,
        "footprint_side_m": round(side, 2),
    }
