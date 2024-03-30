import argparse
from ..utils import machine_config
from ..job_runner import run_jobs 

def parse_args():
    """
    Parses command line arguments.

    Returns:
    argparse.Namespace: The parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description='Run scripts on a SLURM cluster.')
    parser.add_argument('name', help='Name of the job')
    parser.add_argument('--task_name', required=False, help='Name of the task to be run')

    #TODO add date
    
    # Optional argument for machine configuration
    parser.add_argument('--machine', required=False, help='Machine name to run the jobs (e.g., local, remote_1)')

    # Optional arguments for custom machine configuration
    parser.add_argument('--hostname', required=False, help='Hostname of the remote machine')
    parser.add_argument('--username', required=False, help='Username for SSH login')
    parser.add_argument('--key_path', required=False, help='Path to the SSH private key')
    parser.add_argument('--remote_path', required=False, help='Path to the remote directory where scripts will be run')
    parser.add_argument('--env_command', required=False, help='Command to activate the environment on the remote machine')
    parser.add_argument('--slurm_account', required=False, help='SLURM account to use for job submission')
    

    return parser.parse_args()


def cli():
    import sys, json
    args = parse_args()
    print(json.dumps(vars(args), indent=4))
    sys.exit(0)


def main():
    args = parse_args()
    config = machine_config(args)
    run_jobs(args.name, machine_config=config) # TODO: add date

