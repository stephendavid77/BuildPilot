import os
import re
import yaml
from pathlib import Path
from builders.builder import build_project, get_available_platforms, write_summary_log
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.env_check import check_environment
from builders.builder import append_log

def apply_env_settings(env_file="config/env.yaml"):
    if not os.path.exists(env_file):
        print("⚠️ No env.yaml file found. Skipping environment overrides.")
        return

    with open(env_file) as f:
        env_config = yaml.safe_load(f)

    if not env_config or "env" not in env_config:
        return

    overrides = env_config["env"]

    # Apply environment variables
    for key, val in overrides.items():
        if key == "PATH_PREPEND":
            prepend_paths = ":".join(val)
            os.environ["PATH"] = f"{prepend_paths}:{os.environ.get('PATH', '')}"
        else:
            os.environ[key] = val
            print(f"🔧 Set {key} = {val}")

def load_config(path="config/config.yaml"):
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def log(message, enabled=True):
    if enabled:
        print(f"[INFO] {message}")

def get_final_project_list(config):
    scan_cfg = config.get("scan", {})
    base_dir = scan_cfg.get("base_directory", "projects")
    log_enabled = config.get("logging", {}).get("enabled", True)

    all_dirs = [d for d in os.listdir(base_dir) if Path(base_dir, d).is_dir()]
    include_names = [name.strip() for name in scan_cfg.get("include_names", "").split(",") if name.strip()]
    exclude_names = [name.strip() for name in scan_cfg.get("exclude_names", "").split(",") if name.strip()]
    include_pattern = scan_cfg.get("include_pattern", "")
    exclude_pattern = scan_cfg.get("exclude_pattern", "")

    included = []
    if include_names:
        log(f"📌 Explicitly included repos: {include_names}", log_enabled)
        included = [d for d in all_dirs if d in include_names]
    else:
        for d in all_dirs:
            if exclude_names and d in exclude_names:
                continue
            if include_pattern and not re.match(include_pattern, d):
                continue
            if exclude_pattern and re.match(exclude_pattern, d):
                continue
            included.append(d)

    log(f"\n🧾 Final list of projects to build: {included}\n", log_enabled)
    return included, base_dir

def main():
    apply_env_settings()
    config = load_config()
    scan_cfg = config.get("scan", {})
    log_enabled = config.get("logging", {}).get("enabled", True)

    # 🧪 Print environment info
    print("🔍 Environment Check")
    print("=" * 60)
    env_info = check_environment()
    for line in env_info:
        print(line)
        append_log(line)
    print("=" * 60 + "\n")

    final_projects, base_dir = get_final_project_list(config)
    priority_raw = scan_cfg.get("build_priority", "")
    priority_list = [p.strip() for p in priority_raw.split(",") if p.strip()]

    for project in priority_list:
        if project in final_projects:
            log(f"🔧 Building priority project: {project}", log_enabled)
            build_project(Path(base_dir, project), config)
            final_projects.remove(project)
        else:
            log(f"⚠️ Priority project '{project}' not found or excluded.", log_enabled)

    if final_projects:
        log(f"\n⚙️ Building remaining {len(final_projects)} project(s) in parallel...\n", log_enabled)
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(build_project, Path(base_dir, project), config): project
                for project in final_projects
            }
            for future in as_completed(futures):
                project = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"[ERROR] Failed to build {project}: {e}")

    write_summary_log("build_summary.log")

if __name__ == "__main__":
    main()
