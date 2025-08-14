import os
import re
import yaml
import logging
from pathlib import Path
from builders.builder import build_project, write_summary_log
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.env_check import check_environment

# Configure basic logging for the main script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def apply_env_settings(env_file="config/env.yaml"):
    if not os.path.exists(env_file):
        logging.warning("No env.yaml file found. Skipping environment overrides.")
        return

    with open(env_file) as f:
        env_config = yaml.safe_load(f)

    if not env_config or "env" not in env_config:
        return

    overrides = env_config["env"]
    for key, val in overrides.items():
        if key == "PATH_PREPEND":
            prepend_paths = ":".join(val)
            os.environ["PATH"] = f"{prepend_paths}:{os.environ.get('PATH', '')}"
        else:
            os.environ[key] = str(val)
        logging.info(f"Applied environment setting: {key}={val}")

def load_config(path="config/config.yaml"):
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def get_final_project_list(profile_config):
    """Scans the base directory of the active profile and returns a filtered list of project paths."""
    base_dir = profile_config.get("base_directory")
    if not base_dir or not Path(base_dir).is_dir():
        logging.error(f"Base directory '{base_dir}' not found or not a directory. Check your config.")
        return []

    logging.info(f"Scanning base directory: {base_dir}")
    all_dirs = [p for p in Path(base_dir).iterdir() if p.is_dir()]
    logging.info(f"Found directories: {[p.name for p in all_dirs]}")

    include_names = {name.strip() for name in profile_config.get("include_names", "").split(",") if name.strip()}
    exclude_names = {name.strip() for name in profile_config.get("exclude_names", "").split(",") if name.strip()}
    include_pattern = profile_config.get("include_pattern", "")
    exclude_pattern = profile_config.get("exclude_pattern", "")

    if include_names:
        logging.info(f"Filtering based on `include_names`: {include_names}")
        projects_to_filter = [p for p in all_dirs if p.name in include_names]
    else:
        projects_to_filter = all_dirs

    final_projects = []
    for p in projects_to_filter:
        if p.name in exclude_names:
            logging.info(f"Skipped '{p.name}' due to exclude_names.")
            continue
        if include_pattern and not re.match(include_pattern, p.name):
            logging.info(f"Skipped '{p.name}' as it does not match include_pattern.")
            continue
        if exclude_pattern and re.match(exclude_pattern, p.name):
            logging.info(f"Skipped '{p.name}' as it matches exclude_pattern.")
            continue
        final_projects.append(p)
        logging.info(f"Included '{p.name}' based on filtering rules.")

    logging.info(f"Final list of projects to build: {[p.name for p in final_projects]}")
    return final_projects

def main():
    apply_env_settings()
    config = load_config()

    active_profile_name = config.get("active_profile")
    if not active_profile_name:
        logging.error("`active_profile` not set in config.yaml. Please set it to one of the defined profiles.")
        return

    logging.info("Starting environment check...")
    env_info = check_environment()
    for line in env_info:
        print(line)
    logging.info("Environment check complete.")

    profiles_to_run = []
    if active_profile_name.lower() == 'all':
        logging.info("--- Active profile is 'all'. Running all build profiles. ---")
        profiles_to_run = list(config.get("build_profiles", {}).keys())
    else:
        profiles_to_run = [active_profile_name]

    for profile_name in profiles_to_run:
        profile_config = config.get("build_profiles", {}).get(profile_name)
        if not profile_config:
            logging.error(f"Configuration for profile '{profile_name}' not found in `build_profiles`. Skipping.")
            continue

        logging.info(f"--- Using build profile: {profile_name} ---")
        
        # Create a config copy for the current profile context
        current_config = config.copy()
        current_config['active_profile'] = profile_name

        all_projects = get_final_project_list(profile_config)
        priority_list = {p.strip() for p in profile_config.get("build_priority", "").split(",") if p.strip()}
        
        priority_projects = [p for p in all_projects if p.name in priority_list]
        remaining_projects = [p for p in all_projects if p.name not in priority_list]

        for project_path in priority_projects:
            logging.info(f"Building priority project: {project_path.name} (Profile: {profile_name})")
            build_project(project_path, current_config)

        if remaining_projects:
            logging.info(f"Building remaining {len(remaining_projects)} project(s) in parallel for profile '{profile_name}'...")
            with ThreadPoolExecutor() as executor:
                futures = {executor.submit(build_project, p, current_config): p for p in remaining_projects}
                for future in as_completed(futures):
                    project_path = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"An error occurred while building {project_path.name} (Profile: {profile_name}): {e}")

    write_summary_log("build_summary.md")
    logging.info("Build process finished. Summary report generated at build_summary.md")

if __name__ == "__main__":
    main()
