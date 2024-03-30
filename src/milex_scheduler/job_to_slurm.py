import os
from datetime import datetime
from .utils import make_script_name, load_config


__all__ = ["create_slurm_script"]


def create_slurm_script(job_name: str, date: datetime, job_details: dict, machine_config: dict) -> str:
    """Creates a SLURM script and saves it locally"""
    user_settings = load_config()
    path = os.path.join(user_settings['local']['path'], "slurm")
    script_name = make_script_name(job_name, date, job_details)
    # Save the script locally
    path = os.path.join(path, script_name)
    with open(path, 'w') as f:
        write_slurm_script_content(f, job_details, machine_config)
    print(f"Saved SLURM script for task {job_details['name']} saved to {path}")
    return script_name


def write_slurm_script_content(file, job_details: dict, machine_config: dict) -> None:
    """
    Writes the content of the SLURM script with formatted arguments, handling list arguments differently based on their type.
    """
    env_command = machine_config.get('env_command', '')
    slurm_account = machine_config.get('slurm_account', '')

    file.write("#!/bin/bash\n")
    if slurm_account:
        file.write(f"#SBATCH --account={slurm_account}\n")
    output_dir = os.path.join(machine_config['path'], "slurm")
    file.write(f"#SBATCH --output={os.path.join(output_dir, '%x-%j.out')}\n")
    file.write(f"#SBATCH --job-name={job_details['name']}\n")

    # SLURM directives
    for key, value in job_details['slurm'].items():
        if value is not None:
            file.write(f"#SBATCH --{key.replace('_', '-')}={value}\n")
    
    # Make sure path is exported to environment
    file.write(f"export MILEX=\"{machine_config['path']}\"\n")

    # Environment activation command
    if env_command:
        file.write(f"{env_command}\n")

    # Pre-commands
    for cmd in job_details.get("pre_commands", []):
        file.write(f"{cmd}\n")

    # Main command and arguments
    file.write(f"{job_details['script']} \\\n")
    args_keys = list(job_details['args'].keys())
    if args_keys:
        last_arg = args_keys[-1]  # Get the last argument key in case there are arguments

    for k, v in job_details['args'].items():
        if v is None:
            continue
        if isinstance(v, bool):
            if v:  # If True, include the flag without '=True'
                arg_line = f"  --{k}"
            else:
                continue
        elif isinstance(v, list) and all(isinstance(x, (int, float)) for x in v):
            arg_line = f"  --{k} {' '.join(map(str, v))}"
        elif isinstance(v, list):
            arg_line = f"  --{k}"
            for item in v:
                arg_line += f" \\\n    {item}"
        else:
            arg_line = f"  --{k}={v}"

        if k != last_arg:
            arg_line += " \\\n"
        else:
            arg_line += "\n"
        file.write(arg_line)
 
