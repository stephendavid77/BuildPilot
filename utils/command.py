import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command, cwd=None, stream_output=False):
    """
    Executes a command and streams its output in real-time if requested.

    Args:
        command (str): The command to execute.
        cwd (str, optional): The working directory. Defaults to None.
        stream_output (bool, optional): Whether to stream the output in real-time. Defaults to False.

    Returns:
        dict: A dictionary containing the process's exit code, and captured stdout and stderr if not streamed.
    """
    if stream_output:
        try:
            process = subprocess.Popen(command, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    logging.info(output.strip())
            return {"exit_code": process.poll(), "stdout": "", "stderr": ""}
        except Exception as e:
            logging.error(f"Error executing command: {command}\n{e}")
            return {"exit_code": 1, "stdout": "", "stderr": str(e)}
    else:
        try:
            result = subprocess.run(command, shell=True, check=True, cwd=cwd, capture_output=True, text=True)
            return {"exit_code": 0, "stdout": result.stdout.strip(), "stderr": ""}
        except subprocess.CalledProcessError as e:
            return {"exit_code": e.returncode, "stdout": e.stdout.strip(), "stderr": e.stderr.strip()}
