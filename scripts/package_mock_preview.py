"""Build a backend-only permanent mock artefact locally; never upload or deploy."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".verification-local/mock-question-preview"
OVERLAYS = ("mock_preview.py", "mock_questions.py")


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)


def build(output=OUTPUT, revision="HEAD"):
    output = Path(output)
    if output.exists():
        raise RuntimeError("Refusing to overwrite an existing artefact")
    sources = [name for name in git("ls-tree", "-r", "--name-only", revision).decode().splitlines()
               if name.startswith(("api/", "config/", "interview_app_backend/", "shared/"))
               or name in ("pyproject.toml", "vercel.json", ".vercelignore")]
    for name in sources:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git("show", revision + ":" + name))
    overlays = {}
    for name in OVERLAYS:
        source = (ROOT / "deployment" / name).read_bytes()
        overlays["deployment/" + name] = hashlib.sha256(source).hexdigest()
        text = source.decode().replace("from deployment.mock_questions import", "from mock_questions import")
        (output / name).write_text(text, encoding="utf-8")
    index = output / "api/index.py"
    index.write_text("from mock_preview import install\ninstall()\n\n" + index.read_text(), encoding="utf-8")
    (output / "requirements.txt").write_bytes(git("show", revision + ":requirements-backend.txt"))
    inventory = {path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in sorted(output.rglob("*")) if path.is_file()}
    receipt = {"sourceCommit": git("rev-parse", revision).decode().strip(), "overlayFiles": overlays,
               "files": inventory, "fileCount": len(inventory),
               "manifestSha256": hashlib.sha256(json.dumps(inventory, sort_keys=True,
                                                           separators=(",", ":")).encode()).hexdigest()}
    (output.parent / (output.name + "-manifest.json")).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt


if __name__ == "__main__":
    manifest = build()
    print(json.dumps({key: manifest[key] for key in ("sourceCommit", "fileCount", "manifestSha256")}))
