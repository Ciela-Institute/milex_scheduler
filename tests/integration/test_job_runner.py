import os
import pytest
from unittest.mock import patch, MagicMock
from milex_scheduler import save_bundle, run_jobs
from glob import glob

# Mock Data for Job Configurations
mock_job_name = "Test_Job"
mock_jobs = {
    "JobA": {
        "name": "JobA",
        "script": "run_job_a",
        "dependencies": [],
        "slurm": {
            "tasks": 1,
            "cpus_per_task": 1,
            "gres": "gpu:1",
            "mem": "4G",
            "time": "01:00:00",
        },
        "args": {"param1": "value1", "param2": "value2"},
    },
    "JobB": {
        "name": "JobB",
        "script": "run_job_b",
        "dependencies": ["JobA"],
        "slurm": {"tasks": 1, "cpus_per_task": 2, "mem": "8G", "time": "02:00:00"},
        "args": {"param1": "value3", "param2": "value4"},
    },
    "JobC": {
        "name": "JobC",
        "script": "run_job_c",
        "dependencies": ["JobA", "JobB"],
        "slurm": {"tasks": 1, "cpus_per_task": 4, "mem": "16G", "time": "03:00:00"},
        "args": {"param1": "value5", "param2": "value6"},
        "pre_commands": ["echo 'Starting Job C'"],
    },
}

# Mock of submitting jobs to SLURM
mock_job_ids = {"JobA": "12345", 
                "JobB": "67890", 
                "JobC": "54321"}

expected_bundle_content = {
        "JobA": [
            "#!/bin/bash\n",
            "#SBATCH --output=/path/to/remote/slurm/%x-%j.out\n",
            "#SBATCH --job-name=JobA\n",
            "#SBATCH --tasks=1\n",
            "#SBATCH --cpus-per-task=1\n",
            "#SBATCH --gres=gpu:1\n",
            "#SBATCH --mem=4G\n",
            "#SBATCH --time=01:00:00\n",
            "export MILEX=\"/path/to/remote\"\n",
            "source /path/to/remote/venv/bin/activate\n", # Environment activation command is added if provided
            "run_job_a \\\n",
            "  --param1=value1 \\\n",
            "  --param2=value2\n"
        ],
        "JobB": [
            "#!/bin/bash\n",
            f"#SBATCH --dependency=afterok:{mock_job_ids['JobA']}\n",
            "#SBATCH --output=/path/to/remote/slurm/%x-%j.out\n",
            "#SBATCH --job-name=JobB\n",
            "#SBATCH --tasks=1\n",
            "#SBATCH --cpus-per-task=2\n",
            "#SBATCH --mem=8G\n",
            "#SBATCH --time=02:00:00\n",
            "export MILEX=\"/path/to/remote\"\n",
            "source /path/to/remote/venv/bin/activate\n", # Environment activation command is added if provided
            "run_job_b \\\n",
            "  --param1=value3 \\\n",
            "  --param2=value4\n"
        ],
        "JobC": [
            "#!/bin/bash\n",
            f"#SBATCH --dependency=afterok:{mock_job_ids['JobA']}:{mock_job_ids['JobB']}\n",
            "#SBATCH --output=/path/to/remote/slurm/%x-%j.out\n",
            "#SBATCH --job-name=JobC\n",
            "#SBATCH --tasks=1\n",
            "#SBATCH --cpus-per-task=4\n",
            "#SBATCH --mem=16G\n",
            "#SBATCH --time=03:00:00\n",
            "export MILEX=\"/path/to/remote\"\n", # Added automatically in every script
            "source /path/to/remote/venv/bin/activate\n", # Environment activation command is added if provided
            "echo 'Starting Job C'\n", # Pre-commands are added between the environment activation and the main command
            "run_job_c \\\n",
            "  --param1=value5 \\\n",
            "  --param2=value6\n"
        ]
    }


# Mock Machine Config
mock_machine_config = {
    "hostname": "remote.host",
    "username": "user",
    "key_path": "/path/to/key",
    "env_command": "source /path/to/remote/venv/bin/activate",
    "path": "/path/to/remote"
}

def setup_mock_ssh_client() -> MagicMock:
    """Sets up a mock SSH client for testing purposes."""
    mock_ssh_instance = MagicMock()
    mock_stdin = MagicMock()
    mock_stdout = MagicMock()
    mock_stderr = MagicMock()

    # Define the behavior of exec_command to cycle through job IDs
    def mock_exec_command(cmd):
        job = os.path.split(cmd)[-1]
        # Get the job name out of script name, which is {job_name}_{date}_{job_name}.sh
        job_name = job.split('_')[-2].split('.')[0] # See make_script_name in scheduler/utils.py, job_name is saved as the second to last element
        job_id = mock_job_ids[job_name]
        # Update the return value of read each time exec_command is called
        mock_stdout.read.return_value = f"Submitted batch job {job_id}".encode('utf-8')
        return mock_stdin, mock_stdout, mock_stderr

    mock_ssh_instance.exec_command = MagicMock(side_effect=mock_exec_command)
    mock_ssh_instance.connect = MagicMock()
    return mock_ssh_instance


@pytest.fixture
def mock_load_config(monkeypatch,  tmp_path):
    mock_config = {"local": {"path": tmp_path}}
    os.makedirs(tmp_path / "jobs", exist_ok=True)
    os.makedirs(tmp_path / "slurm", exist_ok=True)

    # Patch all the instances of load_config to save and load jobs from the tmp_path
    monkeypatch.setattr("milex_scheduler.save_load_jobs.load_config", lambda: mock_config)
    monkeypatch.setattr("milex_scheduler.job_to_slurm.load_config", lambda: mock_config)
    monkeypatch.setattr("milex_scheduler.job_dependency.load_config", lambda: mock_config)
    monkeypatch.setattr("milex_scheduler.job_runner.load_config", lambda: mock_config)
    monkeypatch.setattr("milex_scheduler.run_slurm.load_config", lambda: mock_config)
    monkeypatch.setattr("milex_scheduler.utils.load_config", lambda: mock_config)
    
    with patch("milex.load_config", return_value=mock_config) as mock_load_config:
        yield mock_load_config


# Mocking File I/O and Remote SSH interactions
@patch("paramiko.SSHClient", new_callable=lambda: setup_mock_ssh_client)
@patch("milex_scheduler.run_slurm.run_slurm_remotely")
def test_integration_schedule_jobs(
        mock_run_script_remotely,
        mock_ssh_client,
        mock_load_config
        ):
    # Save the mock jobs to a JSON file
    save_bundle(mock_jobs, mock_job_name)
    run_jobs(mock_job_name, machine_config=mock_machine_config)

    # Now check the content of the SLURM scripts  generated
    user_config = mock_load_config()
    milex_path = user_config['local']['path']
    slurm_dir = os.path.join(milex_path, 'slurm')
    
    print(os.listdir(milex_path))
    print(os.listdir(slurm_dir))
    
    files_created = glob(os.path.join(slurm_dir, "*.sh"))
    assert len(files_created) == 3, "Expected 3 SLURM scripts to be created"

    for file in files_created:
        with open(file, 'r') as f:
            script_content = f.readlines()
        # extract job name from file name (see make_script_name in scheduler/utils.py, job_name is saved as the second to last element)
        job_name = os.path.split(file)[-1].split('_')[-2].split('.')[0]
        # Check if the content of the script matches the expected content
        expected_content_lines = expected_bundle_content[job_name]
        for i, (line, expected_line) in enumerate(zip(script_content, expected_content_lines)):
            print(line, expected_line)
            assert line == expected_line, f"Mismatch for job {job_name} script at line {i}"

    

mock_jobs_error = {
    "JobA": {
        "name": "JobA",
        # "script": "run_job_a",
        "dependencies": [],
        "slurm": {
            "tasks": 1,
            "cpus_per_task": 1,
            "gres": "gpu:1",
            "mem": "4G",
            "time": "01:00:00",
        },
        "args": {"param1": "value1", "param2": "value2"},
    },
}
# Mocking File I/O and Remote SSH interactions
@patch("paramiko.SSHClient", new_callable=lambda: setup_mock_ssh_client)
@patch("milex_scheduler.run_slurm.run_slurm_remotely")
def test_integration_schedule_jobs_with_error(
        mock_run_script_remotely,
        mock_ssh_client,
        mock_load_config
        ):
    with pytest.raises(ValueError):
        # Save the mock jobs to a JSON file
        save_bundle(mock_jobs_error, mock_job_name)
        run_jobs(mock_job_name, machine_config=mock_machine_config)
        # Missing script name should raise an error

