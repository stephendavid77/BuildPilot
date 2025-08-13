import subprocess

def run_command(command, cwd=None, capture_output=False):
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=cwd,
                                stdout=subprocess.PIPE if capture_output else None,
                                stderr=subprocess.PIPE if capture_output else None)
        return {
            "stdout": result.stdout.decode().strip() if capture_output else "",
            "stderr": "",
            "error": False
        }
    except subprocess.CalledProcessError as e:
        return {
            "stdout": e.stdout.decode().strip() if capture_output and e.stdout else "",
            "stderr": e.stderr.decode().strip() if capture_output and e.stderr else "Unknown error",
            "error": True
        }