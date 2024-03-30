import pytest
from io import StringIO
from unittest.mock import patch
from milex.scheduler.job_to_slurm import write_slurm_script_content
from milex import load_config


@pytest.fixture
def mock_ssh_client():
    with patch('paramiko.SSHClient') as mock:
        yield mock


def test_write_slurm_script_content():
    job_details = {
        'name': 'test_job',
        'slurm': {'time': '01:00:00', 'partition': 'test-partition'},
        'args': {'arg1': 'value1', 'arg2': [1, 2, 3]},
        'script': 'test-application'
    }
    file = StringIO()

    user_settings = load_config()
    machine_config = user_settings["local"]
    write_slurm_script_content(file, job_details, machine_config)


    content = file.getvalue()
    assert "#SBATCH --time=01:00:00" in content
    assert "#SBATCH --partition=test-partition" in content
    assert "test-application" in content
    assert "--arg1=value1" in content
    assert "--arg2 1 2 3" in content


@pytest.mark.parametrize("conditional_flag, expected_line", [
    (True, "  --conditional"),  # Test for boolean True
    (False, ""),  # Test for boolean False, should result in no line
])
def test_write_slurm_script_boolean_flag(conditional_flag, expected_line):
    job_details = {
        'name': 'boolean_flag_test',
        'slurm': {},
        'args': {'conditional': conditional_flag},
        'script': 'test-boolean-application'
    }
    file = StringIO()

    user_settings = load_config()
    machine_config = user_settings["local"]
    write_slurm_script_content(file, job_details, machine_config)

    content = file.getvalue()
    print(content)
    assert expected_line in content, f"Conditional flag handling failed for {conditional_flag}"

def test_write_slurm_script_with_none_value():
    job_details = {
        'name': 'none_value_test',
        'slurm': {},
        'args': {'arg_with_none': None},  # Test handling None value
        'script': 'test-none-application'
    }
    file = StringIO()

    user_settings = load_config()
    machine_config = user_settings["local"]
    write_slurm_script_content(file, job_details, machine_config)

    content = file.getvalue()
    print(content)
    assert "--arg_with_none=None" not in content, "None value should not be included in the script"

def test_write_slurm_script_with_pre_commands_and_env_command():
    job_details = {
        'name': 'pre_commands_test',
        'slurm': {},
        'args': {},
        'script': 'test-pre-commands-application',
        'pre_commands': ['module load python', 'module load cuda']
    }
    file = StringIO()

    user_settings = load_config()
    machine_config = user_settings["local"]
    machine_config['env_command'] = 'source activate test-env'
    write_slurm_script_content(file, job_details, machine_config)

    content = file.getvalue()
    print(content)
    assert "module load python" in content
    assert "module load cuda" in content
    assert "source activate test-env" in content

def test_write_slurm_script_output_dir_customization():
    job_details = {
        'name': 'output_dir_test',
        'slurm': {'output': 'custom-output-%j.txt'},
        'args': {},
        'script': 'test-output-dir-application'
    }
    file = StringIO()

    user_settings = load_config()
    machine_config = user_settings["local"]
    write_slurm_script_content(file, job_details, machine_config)

    content = file.getvalue()
    assert "#SBATCH --output=custom-output-%j.txt" in content, "Custom output directory setting failed"


