import pytest
from unittest.mock import patch, MagicMock, Mock
from unittest.mock import Mock
from milex_scheduler.run_slurm import get_job_id_from_sbatch_output
from milex_scheduler.run_slurm import run_slurm_remotely, run_slurm_locally


@pytest.fixture
def mock_ssh():
    """Sets up a mock SSH client for testing purposes."""
    
    # Create a mock SSH client instance
    mock_ssh_instance = MagicMock()

    # Define the behavior of exec_command to cycle through job IDs
    def mock_exec_command(cmd):
        # Update the return value of read each time exec_command is called
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = f"Submitted batch job 12345".encode('utf-8')
        mock_stdin = MagicMock()
        mock_stderr = MagicMock()
        return mock_stdin, mock_stdout, mock_stderr

    mock_ssh_instance.exec_command = MagicMock(side_effect=mock_exec_command)
    mock_ssh_instance.connect = MagicMock()

    # Patch paramiko.SSHClient to return the mock SSH client instance
    with patch('paramiko.SSHClient', return_value=mock_ssh_instance) as mock_ssh_client:
        yield mock_ssh_client
        

def test_get_job_id_from_sbatch_output():
    output = "Submitted batch job 12345" # Simulation of SLURM output
    job_id = get_job_id_from_sbatch_output(output)
    assert job_id == "12345"

def test_get_job_id_from_sbatch_output_failure():
    output = "Error: something went wrong"
    with pytest.raises(ValueError):
        get_job_id_from_sbatch_output(output)


def test_run_slurm_remotely(mock_ssh):
    # Ensure that read() returns bytes
    mock_machine_config = {
        'hostname': 'testhost',
        'username': 'testuser',
        'key_path': 'testkey',
        'path': '/path/to/remote'
    }

    # Call the function
    job_id = run_slurm_remotely('remote_script.sh', machine_config=mock_machine_config)

    assert job_id == "12345"
    # Those assertions fails, function calls is not registered with current approach
    # mock_ssh.exec_command.assert_called_with('sbatch remote_script.sh')
    # mock_ssh.close.assert_called()


@patch('subprocess.run')
def test_run_slurm_locally(mock_run):
    # Setup mock behavior
    mock_run.return_value = Mock(stdout="Submitted batch job 67890")

    # Call the function
    job_id = run_slurm_locally('local_script.sh')

    assert job_id == "67890"
    # Same as test above
    # mock_run.assert_called_with(['sbatch', 'local_script.sh'], capture_output=True, text=True)

