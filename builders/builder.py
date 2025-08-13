import yaml
from pathlib import Path
from utils.command import run_command

build_logs = []

def append_log(entry):
    build_logs.append(entry)

def write_summary_log(filepath="build_summary.log"):
    with open(filepath, "w") as f:
        f.write("🔧 Build Summary Report\n")
        f.write("="*60 + "\n\n")
        for entry in build_logs:
            f.write(entry + "\n")
        f.write("\n✅ End of report\n")

def load_type_config(project_type):
    try:
        with open(f"config/{project_type}.yaml", 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return None

def get_available_platforms(config_dir="config"):
    return {
        f.stem: f for f in Path(config_dir).glob("*.yaml")
        if f.stem != "config"
    }

def detect_project_type(project_path):
    entries = [p.name for p in project_path.iterdir()]
    available_configs = get_available_platforms()

    for project_type, config_path in available_configs.items():
        type_config = load_type_config(project_type)
        if not type_config:
            continue
        indicators = type_config.get("indicators", [])
        if any(ind in entries for ind in indicators):
            return project_type
    return None

def build_project(project_path, config):
    log_enabled = config.get("logging", {}).get("enabled", True)
    project_name = project_path.name
    entry = [f"📦 Project: {project_name}"]

    project_type = detect_project_type(project_path)
    if not project_type:
        entry.append(f"❌ Skipped: Unknown project type")
        append_log("\n".join(entry))
        return

    entry.append(f"🧩 Detected type: {project_type}")
    type_config = load_type_config(project_type)
    if not type_config:
        entry.append(f"❌ Skipped: No config found for type")
        append_log("\n".join(entry))
        return

    git_cmd = type_config.get("git_command")
    if git_cmd:
        entry.append(f"⬇️ Git command: {git_cmd}")
        result = run_command(git_cmd, cwd=project_path, capture_output=True)
        if result["error"]:
            entry.append(f"⚠️ Git error: {result['stderr']}")

    build_cmds = type_config.get("build_commands", [])
    if not build_cmds:
        build_cmd = type_config.get("build_command")
        if build_cmd:
            build_cmds = [build_cmd]

    for cmd in build_cmds:
        entry.append(f"🔧 Build: {cmd}")
        result = run_command(cmd, cwd=project_path, capture_output=True)
        if result["error"]:
            entry.append(f"❌ Build failed: {result['stderr']}")
            append_log("\n".join(entry))
            return

    entry.append(f"✅ Build status: Success")
    append_log("\n".join(entry))