"""Package a reviewable backend-only free-test artifact; never upload/deploy."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".verification-local/free-model-preview"
OVERLAYS = ("free_model_budget.py", "free_model_transport.py", "live_verification_gate.py", "redis_endpoint_guard.py")


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)


def build():
    if OUTPUT.exists():
        raise RuntimeError("Use the existing manifest; do not overwrite an artifact")
    sources = [name for name in git("ls-files").decode().splitlines()
               if name.startswith(("api/", "config/", "interview_app_backend/", "shared/"))
               or name in ("pyproject.toml", "vercel.json", ".vercelignore")]
    for name in sources:
        target = OUTPUT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git("show", "HEAD:" + name))
    for name in OVERLAYS:
        source = (ROOT / "deployment" / name).read_text(encoding="utf-8")
        source = source.replace("from deployment import free_model_budget as budget", "import free_model_budget as budget")
        source = source.replace("from deployment.redis_endpoint_guard import", "from redis_endpoint_guard import")
        source = source.replace("from deployment.free_model_transport import", "from free_model_transport import")
        (OUTPUT / name).write_text(source, encoding="utf-8")
    index = OUTPUT / "api/index.py"
    index.write_text("from free_model_transport import install\ninstall()\n\n" + index.read_text()
                     + "\nfrom live_verification_gate import LiveVerificationGate\napp = LiveVerificationGate(app)\n", encoding="utf-8")
    (OUTPUT / "requirements.txt").write_bytes(git("show", "HEAD:requirements-backend.txt"))
    inventory = {path.relative_to(OUTPUT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in sorted(OUTPUT.rglob("*")) if path.is_file()}
    receipt = {"applicationSourceCommit": git("rev-parse", "HEAD").decode().strip(), "files": inventory,
               "manifestSha256": hashlib.sha256(json.dumps(inventory, sort_keys=True,
                                                           separators=(",", ":")).encode()).hexdigest()}
    manifest = OUTPUT.parent / "free-model-manifest.json"
    manifest.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(inventory), "manifestSha256": receipt["manifestSha256"], "uploaded": False}))


if __name__ == "__main__":
    build()
