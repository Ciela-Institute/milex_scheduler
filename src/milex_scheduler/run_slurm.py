import os
import re
import subprocess
import paramiko
from typing import Optional
from .utils import load_config

__all__ = ["get_job_id_from_sbatch_output", "run_slurm_remotely", "run_slurm_locally"]


def get_job_id_from_sbatch_output(output):
    """Extracts the job ID from the output of an sbatch command."""
    match = re.search(r'Submitted batch job (\d+)', output)
    if match:
        return match.group(1)
    else:
        raise ValueError(f"Unable to capture job ID from sbatch output {output}")


def run_slurm_remotely(slurm_name, machine: Optional[str] = None, machine_config: Optional[dict] = None):
    """
    Runs a SLURM script on a remote machine via SSH and captures the job ID.

    Args:
        slurm_name (str): The name of the SLURM script to run.
        machine (Optional[str]): The name of the machine to run the script on.
        machine_config (Optional[dict]): The configuration details for the remote machine.

    Returns:
        str: The job ID assigned by SLURM.

    Raises:
        paramiko.SSHException: If there is an error with the SSH connection.
    """
    if machine is not None:
        machine_config = load_config().get(machine)
        if not machine_config:
            raise EnvironmentError(f"No configuration found for machine: {machine}")
    elif machine_config is not None:
        assert 'hostname' in machine_config, "Machine configuration must contain a hostname"
        assert 'username' in machine_config, "Machine configuration must contain a username"
        assert 'key_path' in machine_config, "Machine configuration must contain a key_path for the SSH key"
        machine = machine_config.get('hostname')
    else:
        raise ValueError("Either machine or machine_config must be specified")
    
    hostname, username, key_path = machine_config['hostname'], machine_config['username'], machine_config['key_path']
    script_path = os.path.join(machine_config['path'], "slurm", slurm_name)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, key_filename=key_path)
    stdin, stdout, stderr = ssh.exec_command(f'sbatch {script_path}')
    output = stdout.read().decode('utf-8')
    ssh.close()
    return get_job_id_from_sbatch_output(output)


def run_slurm_locally(slurm_name):
    """Runs a SLURM script locally and captures the job ID."""
    user_config = load_config()
    script_path = os.path.join(user_config['local']['path'], "slurm", slurm_name)
    
    result = subprocess.run(['sbatch', script_path], capture_output=True, text=True)
    return get_job_id_from_sbatch_output(result.stdout)
