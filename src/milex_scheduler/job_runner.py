from typing import Optional
from datetime import datetime
from .job_to_slurm import create_slurm_script
from .job_dependency import update_slurm_script_with_dependencies
from .run_slurm import run_script_remotely, run_script_locally
from .save_load_jobs import load_job, transfer_script_to_remote
from .utils import load_config

__all__ = ["run_job"]


def run_job(job_name: str, machine_config: Optional[dict] = None, date: Optional[datetime] = None):
    """
    Run a job with SLURM either locally or on a remote machine. This is the main function of the scheduler module.
    It assumes the job configuration is stored in a JSON file. The logic to save jobs to a JSON file is implemented in the "save_load_jobs" module.

    Parameters:
    - job_name (str): The name of the job to be scheduled.
    - machine (Optional[str]): The name of the machine where the job should be executed. If not provided, the job will be executed locally.
    - machine_config (Optional[dict]): The configuration details for the remote machine. If not provided, the default configuration will be used.

    Raises:
    - EnvironmentError: If no configuration is found for the specified machine.

    """
    if machine_config is None:
        machine_config = load_config()['local']
    machine = machine_config.get('hostname', 'local') # if no hostname is provided, the job will be executed locally
    
    # Create a SLURM script for each job
    jobs, dependencies, date = load_job(job_name) # List of jobs sorted in tolopological order
    script_names = {}
    for job in jobs:
        if job.get("script", None) is None:
            raise ValueError("'script' entry is missing from one of the jobs in the configuration file {job_name}")
        if job.get("name", None) is None:
            job['name'] = job["script"]
        script_name = create_slurm_script(job_name, date, job, machine_config)
        script_names[job['name']] = script_name
    
    # Submit each job in topological order and capture dependencies in SLURM script
    for job in jobs:
        script_name = script_names[job['name']]
        task_name = job['name']
        if machine != 'local':
            transfer_script_to_remote(script_name, machine_config=machine_config)
            job_id = run_script_remotely(script_name, machine_config=machine_config)
            print(f"Submitted task {task_name} with ID {job_id} on machine {machine_config['hostname']}")
        else:
            job_id = run_script_locally(script_name)
        
        # Update dependent job scripts with the current job ID
        for dependent_job_name in dependencies.get(job['name'], []):
            update_slurm_script_with_dependencies(script_names[dependent_job_name], job_id)

