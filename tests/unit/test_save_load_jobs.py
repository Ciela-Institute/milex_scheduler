from milex_scheduler.save_load_jobs import (
    load_bundle,
    save_job,
    save_bundle,
    transfer_slurm_to_remote,
    nearest_bundle_filename,
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
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="success", stderr="")
        yield mock_run


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
    with patch(
        "milex_scheduler.save_load_jobs.load_config", return_value=mock_config
    ) as mock_load_config:
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


def test_nearest_bundle_file(tmp_path, mock_load_config):
    print(tmp_path)
    job_dir = os.path.join(tmp_path, "jobs")
    os.makedirs(job_dir, exist_ok=True)
    # Create some job files with different dates
    job_files = [
        "job1_20220101000000.json",
        "job1_20220102000000.json",
        "job1_20220103000000.json",
        "job2_20220101000000.json",
        "job2_20220102000000.json",
        "job2_20220103000000.json",
    ]
    for file in job_files:
        file_path = os.path.join(job_dir, file)
        with open(file_path, "w") as f:
            f.write("")

    # Test with desired_date=None
    result, date = nearest_bundle_filename("job1", desired_date=None)
    assert result == "job1_20220103000000.json"

    # Test with desired_date=datetime(2022, 1, 2, 0, 0, 0)
    desired_date = datetime(2022, 1, 2, 0, 0, 0)
    result, date = nearest_bundle_filename("job1", desired_date=desired_date)
    assert result == "job1_20220102000000.json"

    # Test with desired_date=datetime(2022, 1, 1, 0, 0, 0)
    desired_date = datetime(2022, 1, 1, 0, 0, 0)
    result, date = nearest_bundle_filename("job2", desired_date=desired_date)
    assert result == "job2_20220101000000.json"

    # Test with non-existent job name
    with pytest.raises(FileNotFoundError):
        nearest_bundle_filename("job3")


def test_save_job_success(tmp_path, mock_load_config):
    bundle_name = "test_job"
    mock_jobs = {"Job1": {"script": "run-job-1"}, "Job2": {"script": "run-job-2"}}
    now = datetime.now()

    # Set custom user_config path to tmp_path
    save_bundle(mock_jobs, bundle_name)

    files = os.listdir(tmp_path / "jobs")
    assert len(files) == 1
    assert files[0].startswith(bundle_name)
    # Read date from file name with DATE_FORM
    file_name = files[0].split(".")[0]
    file_date = datetime.strptime(file_name.split("_")[-1], DATE_FORMAT)
    assert (
        abs((file_date - now).total_seconds()) < 1
    )  # Check that the date is approximately the same as the current date


def test_save_load_job(tmp_path, mock_load_config):
    # Prepare mock data
    mock_data = {
        "JobA": {"dependencies": [], "script": "run-joba"},
        "JobB": {"dependencies": ["JobA"], "script": "run-jobb"},
        "JobC": {"dependencies": ["JobA", "JobB"], "script": "run-jobc"},
    }
    bundle_name = "dummy_bundle"

    # Save the bundle of jobs
    save_bundle(mock_data, bundle_name)

    # Load back in the bundle
    jobs, dependencies, date = load_bundle(bundle_name)

    print("Jobs", jobs)
    print("Dependency graph", dependencies)

    assert len(jobs) == 3
    assert len(dependencies) == 3
    assert dependencies == {"JobA": ["JobB", "JobC"], "JobB": ["JobC"], "JobC": []}


def test_load_job_topological_sorting(tmp_path, mock_load_config):
    # Prepare mock data
    mock_data = {
        "JobA": {"dependencies": ["JobB"], "script": "run-joba"},
        "JobB": {"dependencies": [], "script": "run-jobb"},
        "JobC": {"dependencies": ["JobA", "JobB"], "script": "run-jobc"},
    }
    bundle_name = "dummy_bundle"

    # Save the bundle of jobs
    save_bundle(mock_data, bundle_name)

    # Load back in the job
    jobs, dependencies, date = load_bundle(bundle_name)

    print("Jobs", jobs)
    print("Dependency graph", dependencies)

    assert len(jobs) == 3
    assert len(dependencies) == 3
    assert dependencies == {"JobB": ["JobC"], "JobA": ["JobC"], "JobC": []}
    assert jobs[0]["name"] == "JobB"
    assert jobs[1]["name"] == "JobA"
    assert jobs[2]["name"] == "JobC"


def test_load_job_file_not_found(tmp_path, mock_load_config):
    bundle_name = "non_existent_bundle"
    with pytest.raises(FileNotFoundError) as excinfo:
        load_bundle(bundle_name)
    assert "No files found" in str(
        excinfo.value
    )  # Test that our error message is being triggered


def test_save_append_jobs_to_bundle(tmp_path, mock_load_config):
    mock_jobA = {"name": "JobA", "dependencies": [], "script": "run-joba"}
    mock_jobB = {"name": "JobB", "dependencies": ["JobA"], "script": "run-jobb"}
    bundle_name = "dummy_bundle"

    # Save jobA
    save_job(mock_jobA, bundle_name)

    # Append jobB to the same bundle
    save_job(mock_jobB, bundle_name, append=True)

    # Load the bundle
    jobs, dependencies, date = load_bundle(bundle_name)

    print("Jobs", jobs)
    print("Dependency graph", dependencies)

    assert len(jobs) == 2
    assert len(dependencies) == 2
    assert dependencies == {"JobA": ["JobB"], "JobB": []}
    assert jobs[0]["name"] == "JobA"
    assert jobs[1]["name"] == "JobB"


def test_save_append_job_to_bundle_with_same_name(tmp_path, mock_load_config):
    mock_jobA = {"name": "JobA", "script": "run-joba"}
    mock_jobB = {"name": "JobA", "script": "run-joba"}
    mock_jobC = {"name": "JobA", "script": "run-joba"}
    bundle_name = "dummy_bundle"

    # Save jobA
    save_job(mock_jobA, bundle_name)

    # Append jobB to the same bundle
    save_job(mock_jobB, bundle_name, append=True)
    save_job(mock_jobC, bundle_name, append=True)

    # Load the bundle
    jobs, dependencies, date = load_bundle(bundle_name)

    print("Jobs", jobs)
    print("Dependency graph", dependencies)

    assert len(jobs) == 3
    assert len(dependencies) == 3
    assert "JobA" in [job["name"] for job in jobs]
    assert "JobA_001" in [job["name"] for job in jobs]
    assert "JobA_002" in [job["name"] for job in jobs]


def test_save_jobs_append_with_same_name(tmp_path, mock_load_config):
    bundle_a = {"JobA": {"script": "run-joba"}, "JobB": {"script": "run-jobb"}}
    bundle_b = {"JobA": {"script": "run-joba"}, "JobB": {"script": "run-jobb"}}

    bundle_name = "dummy_bundle"
    save_bundle(bundle_a, bundle_name)
    save_bundle(bundle_b, bundle_name, append=True)

    jobs, dependencies, date = load_bundle(bundle_name)

    assert len(jobs) == 4
    assert len(dependencies) == 4
    assert "JobA" in [job["name"] for job in jobs]
    assert "JobB" in [job["name"] for job in jobs]
    assert "JobA_001" in [job["name"] for job in jobs]
    assert "JobB_001" in [job["name"] for job in jobs]
    assert dependencies == {"JobA": [], "JobB": [], "JobA_001": [], "JobB_001": []}


def test_save_bundle_type_error(mock_load_config):
    # test bundle not a dict
    bundle_name = "mock"
    bundle = [{"key": "value"}]
    with pytest.raises(TypeError):
        save_bundle(bundle, bundle_name)
    # test bundle not a dict of dict
    bundle = {"key": "value"}
    with pytest.raises(TypeError):
        save_bundle(bundle, bundle_name)


def test_save_bundle_no_script_error(mock_load_config):
    # test bundle not a dict
    bundle_name = "mock"
    bundle = {"JobA": {"dependencies": []}}
    with pytest.raises(KeyError):
        save_bundle(bundle, bundle_name)


def test_save_job_with_same_name_in_append_mode(mock_load_config):
    # Check that new bundle is created with an index appended
    mock_jobA = {"name": "JobA", "script": "run-joba"}
    mock_jobB = {"name": "JobA", "script": "run-joba"}
    bundle_name = "dummy_bundle"

    # Save jobA
    save_job(mock_jobA, bundle_name)

    # Append jobB to the same bundle
    save_job(mock_jobB, bundle_name, append=True)

    # Load the bundle
    jobs, dependencies, date = load_bundle(bundle_name)

    print("Jobs", jobs)

    assert len(jobs) == 2
    assert sorted([job["name"] for job in jobs]) == ["JobA", "JobA_001"]


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

    transfer_slurm_to_remote("test_job", machine_config=mock_machine_config)


def test_transfer_script_to_remote_no_config_raises_error(mock_load_config):
    job_name = "job_name"
    with pytest.raises(ValueError) as excinfo:
        transfer_slurm_to_remote(job_name)
    assert "Either machine_name or machine_config must be specified" in str(
        excinfo.value
    )


def test_transfer_script_to_remote_no_machine_found_raises_error(mock_load_config):
    job_name = "job_name"
    machine_name = "non_existent_machine"
    with patch("milex_scheduler.load_config", return_value={}):
        with pytest.raises(EnvironmentError) as excinfo:
            transfer_slurm_to_remote(job_name, machine_name=machine_name)
        assert "No configuration found for machine" in str(excinfo.value)
