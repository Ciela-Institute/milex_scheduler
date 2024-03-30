import argparse
import subprocess
import shlex
import json
import sys
from milex.scheduler import save_jobs, run_jobs
from ..utils import machine_config


def parse_job_args(job_name, unknown_args) -> dict:
    # Each argument needs to be properly quoted to handle spaces and special characters
    prepared_args = [shlex.quote(arg) for arg in unknown_args]

    # Run the job specific CLI parser to validate the arguments
    command = [f"{job_name}-cli"] + prepared_args
    result = subprocess.run(command, capture_output=True, text=True)
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    
    except subprocess.CalledProcessError as e:
        # Print more intuitive error message
        error_message = (
            f"Failed to execute command: {' '.join(command)}\n"
            f"Exit code: {e.returncode}\n"
            f"Error output: {e.stderr}\n"
            "Please check the above command and error output to diagnose the issue."
        )
        print(error_message)
        # Optionally, you can log this error message to a log file for further analysis
        sys.exit(1)

    try:
        args_dict = json.loads(result.stdout)
    except:
        raise ValueError(f"Error parsing the output of the {job_name}-cli command. Please make sure it prints to the command line "
                         "a valid JSON object (e.g. using 'print(json.dumps(vars(args), indent=4))').")
    return args_dict


def parse_args():
    # fmt: off
    parser = argparse.ArgumentParser(description='Schedule a job to run on a SLURM cluster')
    
    parser.add_argument('name', help='Name of the job')
    # parser.add_argument('--task_name', required=False, help='Name of the task')
    parser.add_argument('--run-now', action='store_true', help='Run the job immediately')

    # Optional argument for machine configuration
    parser.add_argument('--machine', required=False, help='Machine name to run the jobs (e.g., local, remote_1)')
    
    parser.add_argument('--dependencies', required=False, nargs='+', help='List of job names that this job depends on to run')
    parser.add_argument('--pre-commands', required=False, nargs="+", help='Command to run before the main job')
    
    slurm = parser.add_argument_group('slurm', 'SLURM configuration options')
    slurm.add_argument('--array', required=False, help='Array job configuration (e.g., 1-10)')
    slurm.add_argument('--tasks', required=False, type=int, help='Number of tasks to run')
    slurm.add_argument('--cpus_per_task', required=False, type=int, help='Number of CPUs per task')
    slurm.add_argument('--gres', required=False, help='Generic resource specification (e.g., gpu:1)')
    slurm.add_argument('--mem', required=False, help='Memory per node')
    slurm.add_argument('--time', required=True, help='Maximum time for the job to run (e.g., 01:00:00)')


    # Optional arguments for custom machine configuration
    machine_config = parser.add_argument_group('machine_config', 'Custom machine configuration options')
    machine_config.add_argument('--hostname', required=False, help='Hostname of the remote machine')
    machine_config.add_argument('--username', required=False, help='Username for SSH login')
    machine_config.add_argument('--key_path', required=False, help='Path to the SSH private key')
    machine_config.add_argument('--remote_path', required=False, help='Path to the remote directory where scripts will be run')
    machine_config.add_argument('--env_command', required=False, help='Command to activate the environment on the remote machine')
    machine_config.add_argument('--slurm_account', required=False, help='SLURM account to use for job submission')
    machine_config.add_argument('--path', required=False, help='Path to the directory where scripts will be run')
    # fmt: on
    
    args, unknown_args = parser.parse_known_args()

    
    job_args = parse_job_args(args.name, unknown_args)
    return args, job_args


def cli():
    import sys, json
    args, job_args = parse_args()
    if job_args is None:
        sys.exit(1)
    print(json.dumps(vars(args), indent=4))
    sys.exit(0)


def main():
    args, job_args = parse_args()
    # if args.task_name is None:
        # args.task_name = args.name
    # Construct the JSON file
    job_config = {
        args.name: {
            "args": job_args,
            # "name": args.task_name,
            "name": args.name,
            "script": args.name, # Name of the script, in schedule we assume it's the same as task name
            "dependencies": args.dependencies,
            "pre-commands": args.pre_commands,
            "slurm": {
                "array": args.array,
                "tasks": args.tasks,
                "cpus_per_task": args.cpus_per_task,
                "gres": args.gres,
                "mem": args.mem,
                "time": args.time,
            },
        }
    }
    
    save_jobs(job_config, args.name)
    
    if args.run_now:
        config = machine_config(args)
        print(config)
        run_jobs(args.name, machine_config=config)

