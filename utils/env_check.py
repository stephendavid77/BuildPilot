import os
import shutil
import subprocess

def check_environment():
    env_info = []

    java_home = os.environ.get("JAVA_HOME", "❌ Not set")
    maven_home = os.environ.get("MAVEN_HOME", "❌ Not set")

    env_info.append(f"🔍 JAVA_HOME: {java_home}")
    env_info.append(f"🔍 MAVEN_HOME: {maven_home}")

    java_path = shutil.which("java") or "❌ java not found in PATH"
    mvn_path = shutil.which("mvn") or "❌ mvn not found in PATH"

    env_info.append(f"📌 java location: {java_path}")
    env_info.append(f"📌 mvn location: {mvn_path}")

    # Optional: print actual versions
    try:
        java_ver = subprocess.check_output("java -version", shell=True, stderr=subprocess.STDOUT).decode().strip()
        env_info.append("📦 Java Version:\n" + java_ver)
    except Exception as e:
        env_info.append(f"⚠️ Unable to detect Java version: {e}")

    try:
        mvn_ver = subprocess.check_output("mvn -v", shell=True, stderr=subprocess.STDOUT).decode().strip()
        env_info.append("📦 Maven Version:\n" + mvn_ver)
    except Exception as e:
        env_info.append(f"⚠️ Unable to detect Maven version: {e}")

    return env_info