from argparse import Namespace
from .definitions import CONFIG_FILE_PATH, MACHINE_KEYS, DATE_FORMAT
from datetime import datetime
import os
import json


__all__ = ["load_config", "machine_config"]


def make_script_name(job_name, date: datetime, job_details):
    task_name = job_details["name"]
    if task_name == job_name:
        return f"{job_name}_{date.strftime(DATE_FORMAT)}.sh"
    else:
        return f"{job_name}_{task_name}_{date.strftime(DATE_FORMAT)}.sh"


def update_job_info_with_id(job_name, date, task_name, job_id):
    """Updates the job JSON file with the job ID"""
    path = os.path.join(
        load_config()["local"]["path"],
        "jobs",
        f"{job_name}_{date.strftime(DATE_FORMAT)}.json",
    )
    with open(path, "r") as f:
        jobs = json.load(f)
    jobs[task_name]["id"] = job_id
    with open(path, "w") as f:
        json.dump(jobs, f, indent=4)


def load_config() -> dict:
    """
    Loads the configuration file.

    Returns:
    dict: The loaded configuration.

    Raises:
    EnvironmentError: If the configuration file is not found.
    """
    if not os.path.exists(CONFIG_FILE_PATH):
        raise EnvironmentError(f"Configuration file not found at {CONFIG_FILE_PATH}. Please use `milex-configurations` to create the configurations for milex.")
    with open(CONFIG_FILE_PATH, 'r') as file:
        return json.load(file)



def machine_config(args: Namespace):
    machine_config = {}
    if args.machine is not None:
        config = load_config()
        if not config.get(args.machine):
            raise EnvironmentError(
                f"No configuration found for machine: {args.machine}"
            )
        machine_config.update(config.get(args.machine))
    else:
        if args.hostname is not None:
            for key in MACHINE_KEYS:
                if getattr(args, key) is None:
                    raise AttributeError(
                        f"Custom machine configuration requires {key}."
                    )
            machine_config.update({key: getattr(args, key) for key in MACHINE_KEYS})
        else:
            machine_config = load_config()["local"]
    
    # Update the machine configuration with custom parameters for enviroment, path and slurm account
    for key in ["path", "env_command", "slurm_account"]:
        v = getattr(args, key, None)
        if v is not None:
            machine_config[key] = v

    # Enforce required keys
    if machine_config.get("slurm_account", None) is None:
        raise AttributeError(
            "'slurm_account' account must be provided. Rerun with --slurm_account option or rerun milex-configuration to edit the configuration for the machine."
        )

    if machine_config.get("path", None) is None:
        raise AttributeError(
            "'path' must be provided. Rerun with --path option or rerun milex-configuration to edit the configuration for the machine."
        )

    if machine_config.get("env_command", None) is None:
        raise AttributeError(
            "'env_command' must be provided. Rerun with --env_command option or rerun milex-configuration to edit the configuration for the machine."
        )

    return machine_config

