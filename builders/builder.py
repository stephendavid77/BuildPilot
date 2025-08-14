import yaml
from pathlib import Path
from utils.command import run_command
import logging

# A list to hold structured log entries for the summary report
build_logs = []

def append_log(entry):
    """Appends a structured log entry."""
    build_logs.append(entry)

def write_summary_log(filepath="build_summary.md"):
    """Writes a Markdown-formatted build summary report."""
    with open(filepath, "w") as f:
        f.write("# Build Summary Report\n\n")
        for entry in build_logs:
            f.write(f"## 📦 Project: {entry['project_name']}\n\n")
            f.write(f"- **Project Type**: `{entry.get('project_type', 'N/A')}`\n")
            f.write(f"- **Build Status**: {entry['status']}\n")
            
            if entry.get('commands_executed'):
                f.write("\n**Commands Executed**:\n")
                f.write("```\n")
                for cmd in entry['commands_executed']:
                    f.write(f"{cmd}\n")
                f.write("```\n")

            if entry.get('details'):
                f.write("\n**Details**:\n")
                f.write("```\n")
                f.write(entry['details'])
                f.write("\n```\n")
            f.write("\n---\n")

def load_type_config(project_type):
    """Loads build configuration for a given project type."""
    try:
        with open(f"config/{project_type}.yaml", 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.warning(f"No config file found for project type: {project_type}")
        return None

def build_project(project_path, config):
    """Builds a single project based on the active profile and logs the process."""
    project_name = project_path.name
    log_entry = {"project_name": project_name, "status": "", "details": "", "commands_executed": []}

    logging.info(f"--- Starting build for project: {project_name} ---")

    project_type = config.get("active_profile")
    if not project_type:
        log_entry.update({"status": "❌ Skipped", "details": "Could not determine project type from active_profile."})
        append_log(log_entry)
        logging.error(f"Skipping project {project_name}: `active_profile` is not set in the main config.")
        return

    log_entry["project_type"] = project_type
    logging.info(f"Project type for {project_name} is '{project_type}' (from active profile).")

    type_config = load_type_config(project_type)
    if not type_config:
        log_entry.update({"status": "❌ Skipped", "details": f"No config file found for type '{project_type}'"})
        append_log(log_entry)
        logging.warning(f"Skipping project {project_name}: No config file found for type '{project_type}'.")
        return

    if "repo_configurations" in type_config:
        repo_config = next((c for c in type_config.get("repo_configurations", []) if c.get("repo_name") == project_name), None)
        if not repo_config:
            repo_config = next((c for c in type_config.get("repo_configurations", []) if "repo_name" not in c), None)
            if repo_config:
                logging.info(f"Using default '{project_type}' configuration for '{project_name}'.")

        if repo_config and "builds" in repo_config:
            for build in repo_config["builds"]:
                build_dir = project_path / build.get("directory", ".")
                if not build_dir.is_dir():
                    logging.warning(f"Directory '{build.get('directory')}' not found in '{project_name}'. Skipping.")
                    continue
                
                for cmd in build.get("commands", []):
                    log_entry["commands_executed"].append(f"({build.get('directory', '.')}) $ {cmd}")
                    result = run_command(cmd, cwd=build_dir, stream_output=True)
                    if result["exit_code"] != 0:
                        error_details = f"Command failed in '{build.get('directory', '.')}': {cmd}\\{result['stderr']}"
                        log_entry.update({"status": "❌ Failed", "details": error_details})
                        append_log(log_entry)
                        return
            log_entry["status"] = "✅ Success"
            append_log(log_entry)
            return

    build_cmds = type_config.get("build_commands", [])
    for cmd in build_cmds:
        log_entry["commands_executed"].append(f"($) {cmd}")
        result = run_command(cmd, cwd=project_path, stream_output=True)
        if result["exit_code"] != 0:
            error_details = f"Command failed: {cmd}\\{result['stderr']}"
            log_entry.update({"status": "❌ Failed", "details": error_details})
            append_log(log_entry)
            return

    log_entry["status"] = "✅ Success"
    append_log(log_entry)
