"""
Utility functions to save/load jobs to/from a JSON file in the jobs directory
"""
from .utils import load_config
from .definitions import DATE_FORMAT
from .job_dependency import dependency_graph
from typing import Optional
from graphlib import TopologicalSorter
from datetime import datetime
import paramiko
import json
import os

__all__ = ["save_task", "save_job", "load_job", "transfer_script_to_remote", "nearest_job_file"]


def save_job(
        job_details: dict, 
        job_name: str, 
        append: bool = False,
        ) -> None:
    """
    Save job configurations to a JSON file.

    Args:
        job_details (dict): A dict of tasks configurations.
        job_name (str): The name of the job to save.
        append (bool): Flag indicating whether to append the job configuration to an existing file. Defaults to False.
    """
    user_config = load_config()
    if append:
        try: # Save the job in existing job file
            file_path, date = nearest_job_file(job_name, desired_date)
            # Load the job file
            with open(file_path, 'r') as file:
                job = json.load(file)
            # Append the new job to the existing job file and save it
            job.update(job_details)
        except FileNotFoundError: # Create a new job file
            now = datetime.now().strftime(DATE_FORMAT)
            file_path = os.path.join(user_config['local']['path'], 'jobs', f'{job_name}_{now}.json')
            job = job_details
    else: # Create a new job file
        now = datetime.now().strftime(DATE_FORMAT)
        file_path = os.path.join(user_config['local']['path'], 'jobs', f'{job_name}_{now}.json')
        job = job_details
    
    # Save the job to a JSON file
    with open(file_path, 'w') as file:
        json.dump(job, file, indent=4)

    print(f"Saved job {job_name} to {file_path}")


def save_task(
        task_detais: dict, 
        job_name: str, 
        task_name: str,
        append: bool = False,
        ) -> None:
    """
    Save job configurations to a JSON file.

    Args:
        task_details (dict): A dict of task configurations.
        job_name (str): The name of the job to save.
        task_name (str): The name of the task.
        append (bool): Flag indicating whether to append the task configuration to an existing file. Defaults to False.
    """
    user_config = load_config()
    if append:
        try: # Save the task in existing job file
            file_path, date = nearest_job_file(job_name, desired_date)
            # Load the job file
            with open(file_path, 'r') as file:
                job = json.load(file)
            # Append the new job to the existing job file and save it
            job[task_name] = job_details
        except FileNotFoundError: # Create a new job file
            date = datetime.now().strftime(DATE_FORMAT)
            file_path = os.path.join(user_config['local']['path'], 'jobs', f'{job_name}_{date}.json')
            job = {task_name: task_details}
    else: # Create a new job file
        date = datetime.now().strftime(DATE_FORMAT)
        file_path = os.path.join(user_config['local']['path'], 'jobs', f'{job_name}_{date}.json')
        job = {task_name: task_details}

    # Save the job to a JSON file
    with open(file_path, 'w') as file:
        json.dump(job, file, indent=4)
        
    print(f"Saved job {job_name} to {file_path}")


def transfer_script_to_remote(script_name, machine_name: Optional[str] = None, machine_config: Optional[dict] = None) -> None:
    """
    Transfers a script from the local machine to a remote machine.
    """
    user_config = load_config()
    local_script_path = os.path.join(user_config['local']['path'], "slurm", script_name)
    
    if machine_name is not None:
        machine_config = user_config.get(machine_name)
        if not machine_config:
            raise EnvironmentError(f"No configuration found for machine: {machine_name}")
    if machine_config is None:
        raise ValueError("Either machine_name or machine_config must be specified")
    if machine_config.get('path', None) is None:
        raise ValueError(f"Machine {machine_config['hostname']} configuration must contain a path to the milex directory")
    remote_script_path = os.path.join(machine_config['path'], "slurm", script_name)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(machine_config['hostname'], 
                username=machine_config['username'], 
                key_filename=machine_config['key_path'])

    sftp = ssh.open_sftp()
    sftp.put(local_script_path, remote_script_path)
    sftp.close()
    ssh.close()


def order_tasks(tasks, sorted_names):
    tasks_list = []
    for name in sorted_names:
        task_details = tasks[name]
        task_details['name'] = name  # Make sure name of the task is in details
        tasks_list.append(task_details)
    return tasks_list


def load_job(job_name: str, desired_date: Optional[datetime] = None) -> tuple[list, dict, datetime]:
    """
    Read the jobs JSON file and extract the dependency graph.

    Parameters:
    job_name (str): The name of the job to load.
    topological_sort (bool): Flag indicating whether to perform a topological sort on the dependency graph. 
                             Defaults to True.

    Returns:
    tuple: A tuple containing the loaded jobs and the dependency graph.

    Raises:
    FileNotFoundError: If the specified job file does not exist.
    JSONDecodeError: If the job file is not a valid JSON file.
    """

    # Load user configuration and job file path
    user_config = load_config()
    job_file, date = nearest_job_file(job_name, desired_date)
    file_path = os.path.join(user_config['local']['path'], 'jobs', job_file)

    with open(file_path, 'r') as file:
        try:
            jobs = json.load(file)
        except json.JSONDecodeError as e:
            raise OSError(f"Error decoding the job file {job_name}.json (located in jobs folder). Make sure it is a valid JSON file.")

    dependencies = dependency_graph(jobs)
    
    # Depth-first search topological sorting of a graph (raises error if a cycle is detected)
    sorted_job_names = tuple(TopologicalSorter(dependencies).static_order())[::-1]
    jobs = order_tasks(jobs, sorted_job_names)
    
    return jobs, dependencies, date


def nearest_job_file(job_name: str, desired_date: Optional[datetime] = None) -> tuple[str, datetime]:
    """
    Get the job closest in time to configuration from the jobs directory.
    """
    user_config = load_config()
    job_dir = os.path.join(user_config['local']['path'], 'jobs')
    job_files = [f[:-5] for f in os.listdir(job_dir) if f.startswith(job_name) and f.endswith('.json')]
    if not job_files:
        raise FileNotFoundError(f"No files found with name '{job_name}' in directory {job_dir}")
    dates = []
    for file in job_files:
        try:
            file_date = datetime.strptime(file.split('_')[-1], DATE_FORMAT)
            dates.append(file_date)
        except:
            print(f"Could not parse date from file {file}. Name of file expected to have the format 'job_name_{DATE_FORMAT}.json' this file will not be considered.")
    if desired_date is None:
        desired_date = datetime.now()
    nearest_date = min(dates, key=lambda x: abs(x - desired_date))
    return f"{job_name}_{nearest_date.strftime(DATE_FORMAT)}.json", nearest_date
 
