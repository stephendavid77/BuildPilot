# BuildPilot

BuildPilot is an automated, multi-language, profile-based build tool designed to streamline the process of building multiple projects, such as those in a monorepo or a collection of local repositories.

## Core Features

- **Profile-Based Builds**: Define different build profiles for various scenarios (e.g., `daily`, `full_release`, `ci`).
- **Declarative Configuration**: All build logic is defined in simple YAML files, keeping the core script clean and easy to manage.
- **Language-Agnostic**: Easily extendable to support any language or build system by adding a simple language configuration file.
- **Parallel Execution**: Builds non-priority projects in parallel to significantly speed up the overall process.
- **Flexible Project Filtering**: Include or exclude projects using simple name lists or powerful regex patterns.
- **Build Prioritization**: Ensure critical projects are built first in a sequential, predictable order.
- **Environment Customization**: Override or prepend environment variables (like `PATH`) for specific build needs.
- **Automated Summary Reports**: Generates a `build_summary.md` at the end of each run with the status of all attempted builds.

## How it Works

1.  **Load Configuration**: Reads the `active_profile` from `config/config.yaml`.
2.  **Scan Projects**: Scans the `base_directory` defined in the active profile.
3.  **Filter Projects**: Applies `include`/`exclude` rules to create a final list of projects to build.
4.  **Prioritize**: Builds projects listed in `build_priority` sequentially.
5.  **Build in Parallel**: Builds all remaining projects concurrently using a thread pool.
6.  **Detect & Build**: For each project, it detects the language (using `indicators` from `config/<language>.yaml`) and runs the corresponding `build_commands`.
7.  **Report**: Writes a summary of all successes and failures to `build_summary.md`.

## Project Structure

```
BuildPilot/
├── builders/
│   └── builder.py        # Core build logic
├── config/
│   ├── config.yaml       # Main configuration with build profiles
│   ├── env.yaml          # Environment variable overrides
│   └── python.yaml       # Example language-specific config
├── utils/
│   └── env_check.py      # Environment checking utility
├── main.py               # Main entry point
└── README.md
```

## Configuration

BuildPilot is driven by three types of YAML files in the `config/` directory.

### 1. `config.yaml` (Main Configuration)

This is the main control file for the application.

- `active_profile`: The profile to run. Can be a specific profile name or `all` to run every defined profile.
- `build_profiles`: A dictionary where each key is a profile.
  - `base_directory`: The root folder to scan for projects.
  - `include_names` / `exclude_names`: Comma-separated lists of project directory names to explicitly include or exclude.
  - `include_pattern` / `exclude_pattern`: Regex patterns for more advanced filtering of project names.
  - `build_priority`: A comma-separated list of projects to build sequentially before others.

### 2. `<language>.yaml` (Language-Specific Config)

These files define how to build a specific type of project.

- `git_command`: The command to update the project's source code (e.g., `git pull`).
- `indicators`: A list of filenames that identify a project as being of this language (e.g., `setup.py` or `pom.xml`).
- `build_commands`: A list of shell commands to execute to build the project.

**Example: `python.yaml`**
```yaml
git_command: "git pull origin main"
build_commands:
  - "pip install -r requirements.txt"
  - "python setup.py install"
indicators:
  - "setup.py"
  - "requirements.txt"
```

### 3. `env.yaml` (Environment Overrides)

An optional file for setting up the build environment.

- `env`: A dictionary of environment variables to set.
- `PATH_PREPEND`: A special key whose value is a list of paths to prepend to the system's `PATH` variable.

## How to Run

1.  **Install Dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

2.  **Configure:**
    - Edit `config/config.yaml` to define your `build_profiles`.
    - Create language configs (e.g., `java.yaml`, `go.yaml`) as needed in the `config/` directory.

3.  **Execute:**
    ```sh
    python main.py
    ```