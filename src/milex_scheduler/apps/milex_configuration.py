import os
import subprocess
import json
import paramiko
import socket
from ..definitions import CONFIG_FILE_PATH

def expand_path(path):
    """Expand environment variables, the tilde, and the current directory in a file path."""
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))

def setup_directories(base_path, directories, ssh_client=None):
    """Create required directories at the specified base path, locally or remotely."""
    for directory in directories:
        path = os.path.join(base_path, directory)
        command = f'mkdir -p {path}'
        if ssh_client:
            stdin, stdout, stderr = ssh_client.exec_command(command)
            if stderr.readlines():
                print(f"Error creating {path} remotely.")
                print(f"Error message: {stderr.readlines()}")
            else:
                print(f"Created or found existing remote directory: {path}")
        else:
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"Created directory: {path}")
            else:
                print(f"Directory already exists: {path}")

# Updated the shell generator to include the MILEX environment variable
# def update_bashrc(base_path, ssh_client=None):
    # """Append MILEX environment variable to .bashrc for persistence, locally or remotely."""
    # bash_command = f'echo "export MILEX=\\"{base_path}\\"" >> ~/.bashrc'
    # if ssh_client:
        # ssh_client.exec_command(bash_command)
    # else:
        # os.system(bash_command)

def check_host(hostname):
    """Check if the SSH hostname is resolvable."""
    try:
        socket.gethostbyname(hostname)
    except socket.gaierror:
        return False
    return True

def get_git_editor():
    """Get the default editor set in Git's configuration."""
    try:
        return subprocess.check_output(['git', 'config', '--global', 'core.editor'], encoding='utf-8').strip()
    except subprocess.CalledProcessError:
        # Fallback to a default editor if Git's editor is not set
        return 'nano'

def open_editor(file_path):
    """Open the file in Git's default text editor or a fallback editor."""
    editor = get_git_editor()
    subprocess.call([editor, file_path])


def main():
    if os.path.exists(CONFIG_FILE_PATH):
        open_editor(CONFIG_FILE_PATH)
    else:
        example_config = {
            "local": {
                "path": "/path/to/local/milex",
                "env_command": "source /path/to/local/venv/bin/activate",
                "slurm_account": "def-bengioy"
                },
            "remote_machine": {
                "hostname": "remote1.example.com",
                "username": "user1",
                "key_path": "~/.ssh/id1_rsa",
                "path": "/path/to/remote/milex",
                "env_command": "source /path/to/remote/venv/bin/activate",
                "slurm_account": "rrg-account_name"
            }
        }
        with open(CONFIG_FILE_PATH, 'w') as file:
            json.dump(example_config, file, indent=4)
        open_editor(CONFIG_FILE_PATH)

    with open(CONFIG_FILE_PATH, 'r') as file:
        config = json.load(file)

    # Check if local entry is present and has a valid path
    if "local" not in config:
        raise ValueError("Invalid configuration. Please make sure the 'local' machine is present and has a valid 'path'.")
    if "path" not in config["local"] or not os.path.exists(config["local"]["path"]):
        raise ValueError("Invalid configuration. Please make sure the 'local' machine is present and has a valid 'path'.")

    # Handle remote machines setup
    for machine_name, machine_config in config.items():
        if machine_name == "local":
            continue

        if machine_config.get("hostname", None) is None: # local machine
            if machine_config.get("path", None) is not None :
                setup_directories(machine_config["path"], ['data', 'models', 'slurm', 'jobs', 'results'])
                # update_bashrc(machine_config["path"])

        else: # remote machine
            if not check_host(machine_config["hostname"]):
                print(f"Error: Unable to resolve hostname '{machine_config['hostname']}' for {machine_name}.")
                continue
        
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(machine_config["hostname"], username=machine_config["username"], key_filename=expand_path(machine_config["key_path"]))
            
            setup_directories(machine_config["path"], ['data', 'models', 'slurm', 'jobs', 'results'], ssh_client=ssh)
            # update_bashrc(machine_config["path"], ssh_client=ssh)
            ssh.close()

    print("Milex setup is complete.")

