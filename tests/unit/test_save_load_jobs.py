from milex_scheduler.save_load_jobs import (
    load_job,
    save_job,
    save_task,
    transfer_script_to_remote,
    nearest_job_file
)
from milex_scheduler import DATE_FORMAT
from unittest.mock import patch
from unittest.mock import MagicMock
from datetime import datetime
import json
import os
import pytest

"""
Fixtures
"""
@pytest.fixture
def mock_ssh():
    # Create a mock SSH client using Transport and a custom MagicMock
    mock_ssh = MagicMock()

    def create_mock_transport(*args, **kwargs):
        # Create a mock Transport object
        mock_transport = MagicMock()

        # Mock the behavior of the Transport object
        def connect(*args, **kwargs):
            pass  # Mock the connection behavior

        def open_sftp():
            mock_sftp = MagicMock()

            # Mock the SFTP put method
            def put(local_path, remote_path):
                pass  # Mock the put behavior

            mock_sftp.put.side_effect = put
            return mock_sftp

        mock_transport.connect.side_effect = connect
        mock_transport.open_sftp.side_effect = open_sftp

        return mock_transport

    # Patch paramiko.SSHClient in the correct module
    with patch("paramiko.SSHClient", new_callable=MagicMock) as mock_ssh_client:
        mock_ssh_client.return_value.get_transport.side_effect = create_mock_transport

        # Return the mock SSH client
        yield mock_ssh


@pytest.fixture
def mock_job_script(tmp_path):
    # Create a temporary directory and a mock job script inside it
    os.makedirs(tmp_path / "jobs", exist_ok=True)
    job_script_path = tmp_path / "jobs/test_job.sh"
    job_script_path.write_text("#!/bin/bash\n# Mock job script\n")
    return job_script_path


@pytest.fixture
def mock_load_config(tmp_path):
    mock_config = {"local": {"path": tmp_path}}
    os.makedirs(tmp_path / "jobs", exist_ok=True)
    with patch("milex_scheduler.save_load_jobs.load_config", return_value=mock_config) as mock_load_config:
        yield mock_load_config


"""
Test save and load jobs
"""

# Helper functions
def create_mock_job_file(tmp_path, job_name, data):
    now = datetime.now().strftime(DATE_FORMAT)
    file_path = tmp_path / f"jobs/{job_name}_{now}.json"
    with open(file_path, "w") as file:
        json.dump(data, file)
    return file_path


def test_nearest_job_file(tmp_path, mock_load_config):
    print(tmp_path)
    job_dir = os.path.join(tmp_path, 'jobs')
    os.makedirs(job_dir, exist_ok=True)
    # Create some job files with different dates
    job_files = [
        'job1_20220101000000.json',
        'job1_20220102000000.json',
        'job1_20220103000000.json',
        'job2_20220101000000.json',
        'job2_20220102000000.json',
        'job2_20220103000000.json',
    ]
    for file in job_files:
        file_path = os.path.join(job_dir, file)
        with open(file_path, 'w') as f:
            f.write('')
    
    # Test with desired_date=None
    result, date = nearest_job_file('job1', desired_date=None)
    assert result == 'job1_20220103000000.json'
    
    # Test with desired_date=datetime(2022, 1, 2, 0, 0, 0)
    desired_date = datetime(2022, 1, 2, 0, 0, 0)
    result, date = nearest_job_file('job1', desired_date=desired_date)
    assert result == 'job1_20220102000000.json'
    
    # Test with desired_date=datetime(2022, 1, 1, 0, 0, 0)
    desired_date = datetime(2022, 1, 1, 0, 0, 0)
    result, date = nearest_job_file('job2', desired_date=desired_date)
    assert result == 'job2_20220101000000.json'
    
    # Test with non-existent job name
    with pytest.raises(FileNotFoundError):
        nearest_job_file('job3')


def test_save_job_success(tmp_path, mock_load_config):
    job_name = "test_job"
    mock_jobs = {"Task1": {}, "Task2": {}}
    now = datetime.now()

    # Set custom user_config path to tmp_path
    save_job(mock_jobs, job_name)
    
    files = os.listdir(tmp_path / "jobs")
    assert len(files) == 1
    assert files[0].startswith(job_name)
    # Read date from file name with DATE_FORM
    file_name = files[0].split(".")[0]
    file_date = datetime.strptime(file_name.split("_")[-1], DATE_FORMAT)
    assert abs((file_date - now).total_seconds()) < 1 # Check that the date is approximately the same as the current date
    

def test_save_load_job(tmp_path, mock_load_config):
    # Prepare mock data
    mock_data = {
        "JobA": {"dependencies": []},
        "JobB": {"dependencies": ["JobA"]},
        "JobC": {"dependencies": ["JobA", "JobB"]},
    }
    job_name = "dummy_job"
    
    # Save the job
    save_job(mock_data, job_name)

    # Load back in the job
    jobs, dependencies, date = load_job(job_name)
    
    print("Jobs", jobs)
    print("Dependency graph", dependencies)

    assert len(jobs) == 3
    assert len(dependencies) == 3
    assert dependencies == {"JobA": ["JobB", "JobC"], "JobB": ["JobC"], "JobC": []}


def test_load_job_topological_sorting(tmp_path, mock_load_config):
    # Prepare mock data
    mock_data = {
        "JobA": {"dependencies": ["JobB"]},
        "JobB": {"dependencies": []},
        "JobC": {"dependencies": ["JobA", "JobB"]},
    }
    job_name = "dummy_job"

    # Save the job
    save_job(mock_data, job_name)

    # Load back in the job
    jobs, dependencies, date = load_job(job_name)
    
    print("Jobs", jobs)
    print("Dependency graph", dependencies)

    assert len(jobs) == 3
    assert len(dependencies) == 3
    assert dependencies == {"JobB": ["JobC"], "JobA": ["JobC"], "JobC": []}
    assert jobs[0]["name"] == "JobB"
    assert jobs[1]["name"] == "JobA"
    assert jobs[2]["name"] == "JobC"


def test_load_job_file_not_found(tmp_path, mock_load_config):
    job_name = "non_existent_job"
    with pytest.raises(FileNotFoundError) as excinfo:
        load_job(job_name)
    assert "No files found" in str(excinfo.value) # Test that our error message is being triggered


"""
Test transfer script to remote
"""


def test_transfer_script_to_remote(
    tmp_path, mock_ssh, mock_load_config, mock_job_script
):
    mock_machine_config = {
        "hostname": "testhost",
        "username": "testuser",
        "key_path": "testkey",
        "path": "/path/to/remote",
    }

    transfer_script_to_remote("test_job", machine_config=mock_machine_config)


def test_transfer_script_to_remote_no_config_raises_error():
    job_name = "job_name"
    with pytest.raises(ValueError) as excinfo:
        transfer_script_to_remote(job_name)
    assert "Either machine_name or machine_config must be specified" in str(
        excinfo.value
    )


def test_transfer_script_to_remote_no_machine_found_raises_error():
    job_name = "job_name"
    machine_name = "non_existent_machine"
    with patch("milex.load_config", return_value={}):
        with pytest.raises(EnvironmentError) as excinfo:
            transfer_script_to_remote(job_name, machine_name=machine_name)
        assert "No configuration found for machine" in str(excinfo.value)

