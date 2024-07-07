# Milex Scheduler

Milex Scheduler is a package that simplifies the process of scheduling and running jobs on a SLURM cluster. It provides an abstraction layer over the SLURM shell scripts, allowing you to schedule jobs with a single command line interface (CLI) tool.

TODO: Clarify the docs. Should have usage first with simple examples
TODO: Mention the append feature
TODO: mention the key functions that can be used in a package.
TODO: Have a function that runs a job, without necessarily loading it. Might be useful for sampling package?
TODO: A way to handle the machine that does not enter the script in the spirit of reproducibility

## Key Features

- **Simplified Job Scheduling**: Schedule jobs on a SLURM cluster with a single command, without the need to write complex SLURM scripts.
- **Reproducibility**: Job configurations are saved as JSON files, making it easy to reproduce and share job setups.
- **User-Agnostic**: User-specific details like SLURM accounts and virtual environments are abstracted away, ensuring reproducibility across different users.
- **Local and Remote Execution**: Run jobs on both local and remote machines.

## Installation

1. Install the Milex-scheduler package

```bash
git clone git@github.com:Ciela-Institute/milex_scheduler.git
cd milex_scheduler
pip install -e .
```

2. Configure Milex for your environment by running:

```bash
milex-configuration
```

This command will guide you through setting up your local and remote machine configurations, including specifying paths, virtual environments, and SLURM accounts.

## Usage

### Scheduling a Job

To schedule a job, use the `milex-schedule` command:

```bash
milex-schedule your-application \
    --time=00-01:00 \
    --cpus_per_task=1 \
    --gres=gpu:1 \
    --mem=16G
```

This command schedules the `your-application` job to run for 1 hour, using 1 CPU, 1 GPU, and 16GB of memory.

### Running a Job

To run a scheduled job, use the `milex-run` command:

```bash
milex-run your-application --machine=remote_machine
```

This command runs the `your-application` job on the `remote_machine` specified in your configuration. You can also schedule and run at the same time 
using the `--run-now` command
```bash
milex-schedule your-application --run-now
```

## Examples

### Scheduling a Simple Job

1. Register your application in the `pyproject.toml` file:

```toml
[project.scripts]
my-script = "my_package.module:main"
my-script-cli = "my_package.module:cli"
```

2. Schedule the job:

```bash
milex-schedule my-script --time=12-00:00 --cpus_per_task=1
```

3. Run the job:

```bash
milex-run my-script
```

### Scheduling a Job with Dependencies

```bash
milex-schedule my-script \
    --dependencies job1 job2 \
    --time=1-00:00 \
    --cpus_per_task=1 \
    --gres=gpu:1
```

This command schedules `my-script` to run for 1 day, using 1 CPU and 1 GPU, and sets dependencies on `job1` and `job2`.


# Scheduling a script
To ensure smooth integration, your application must adhere to a specific structure and be properly registered within your Python package.

## Application Structure

Your application should consist of at least two main functions: `parse_args()` and `main()`. You should also include the `cli()` function below **as is**. 
Below is a template to guide you in structuring your application correctly.

### CLI Function

Here is an example of an argument parser:
```python

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Your application description here.")
    # Define your arguments here
    parser.add_argument('--example', type=str, help='Example argument')
    args = parser.parse_args()
    return args
```
<!--[See this page for the conventions used in order to integrate your script properly with `milex-schedule`](argument-parser).-->


**You should copy the code below in all your scripts, assuming you also call the function above `parse_args`**.

```python
def cli():
    import sys, json
    args = parse_args()
    print(json.dumps(vars(args), indent=4))
    sys.exit(0)
```

This second function is then registered as an application in the `pyproject.toml` file (see [this section](#Registering-Your-Application)). 
It is separated from the `parse_args` function because we must include a `sys.exit(0)` after successfull completion of `parse_args`.
This allows `milex-schedule` to use `subprocess.run[f"{your-job-name}-cli"]` to parse your job specific arguments.
Finally, the print statement is included there so that `milex-schedule` can capture the output of the `cli` from the command line. 

### Main function

The main() function serves as the entry point of your application. It will call `parse_args()` to parse the command-line arguments and 
then proceed with the application's main logic using these arguments.

```python
def main():
    import ...
    args = parse_args()
    # Application logic goes here
```
No other structure is imposed on your script, other than it be registered as a command line application. If you have import that require running code or
for heavy packages like torch, consider putting these imports in the main function so that `cli` can remain very light. Having heavy import placed at the root
level of the file is the main reason for slow scheduling of jobs.

## Registering Your Application

To make your application accessible as a command-line interface (CLI) tool, you must register it in the `pyproject.toml` file of your package. 
See this [document page](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) if you have never done this.
This registration process allows your application to be run directly from the command line, 
provided that your package and `milex` are installed in the same Python environment.

For the scheduler to work, you must add 2 entries to the `[project.scripts]` section of your pyproject.toml file as follows:

```python
[project.scripts]
your-application = "your_package.module:main"
your-application-cli = "your_package.module:cli"
```
You must do this for each script you want to register and run through the scheduler. Make sure to always append `-cli` to your application name 
to register the `cli` function.


## Scheduling your application

Once the application is registered, you can schedule it using, for example, the following template


```shell
milex-schedule your-application\
    --dependencies job1 job2\
    --pre-commands "cp some_file.txt $SLURM_TMPDIR/" "cp some_other_file.txt $SLURM_TMPDIR/"\
    --time=00-01:00\
    --array=1-10:2\
    --tasks=1\
    --cpus_per_task=1\
    --gres=gpu:1\
    --mem=16G\
```
You can then run this application with
```
milex-run your-application --machine=name_of_machine
```
Or by using the flag `--run-now` and the `--machine` flag in the `milex-schedule` application.
```
milex-schedule your-application --run-now --machine=name_of_machine\
    ...
```

The machine argument is optional, in which case the *local* machine is used.
The name of the machine is one in `.milexconfig` configured with [`milex-configuration`](#Milex-Configuration). 
Below we give the complete list of arguments in case you want to customize a schedule and/or override some of the machine configuration.

**Note**: The slurm account is dealt with through the machine configuration (and so is the virtual environment).

Dependencies is an advanced features which allows you to set a dependence for this job to other jobs. 
The pre-commands allow you to modify the automatically created shell script to include other types of shell commands like 
copying a file to the server where the job is being run etc.


# Milex Configuration

This document provides detailed instructions for configuring Milex to run jobs using SLURM, either on a local machine or a remote cluster via SSH. It includes steps for creating an SSH key to securely access the cluster.

## Setting Up Milex Configuration

Before executing jobs with Milex, it's essential to configure your environment. 
This setup involves specifying SSH credentials, the path to the Milex base directory, and commands to activate your Python virtual environment. 
This configuration automates the handling of user-specific details, such as SLURM account information and virtual environment activation, 
ensuring that Milex scripts are user-agnostic to facilitate result reproduction.

Additionally, the configuration process creates directories for storing job files (JSON files with complete job information for reproducibility) 
and automatically generated SLURM shell scripts. The job JSON file is an abtraction over shell SLURM script.

The directory structure post-configuration will be:

```
├── jobs
│   ├── *name*_*date*.json
├── slurm
│   ├── *name*_*date*_*job_name*.sh
├── models
├── results
└── data
```

### Steps to Configure:

1. **Run the Configuration Script**: After installing the Milex package, execute the configuration script by running the following command:

    ```bash
    milex-configuration
    ```

   This command will open a configuration file in the default text editor of `git` (or `nano` if it is not set) for you to edit.
   
2. **Edit Configuration Details**: The editor will open a JSON file where you can enter your configuration details. Here's what you should specify:
   
    - For each machine (local or remote), provide:
        - `path`: The absolute path to the Milex base directory on the machine.
        - `env_command`: The command to activate the Python virtual environment where Milex is installed.
        - `slurm_account`: The SLURM account to use for job submission (e.g. `def-bengioy`)
        - For remote machines, additionally specify:
            - `hostname`: The hostname or IP address of the remote machine (e.g. `beluga.computecanada.ca`)
            - `username`: Your username on the remote machine.
            - `key_path`: The path to your SSH private key (e.g. `~/.ssh/id_rsa`)
   
   Here is an example structure:

    ```json
    {
        "local_machine": {
            "path": "/path/to/local/directory"
            "env_command": "source /path/to/remote/venv/bin/activate",
            "slurm_account": "def-bengioy"
        },
        "remote_machine": {
            "hostname": "remote1.example.com",
            "username": "user1",
            "key_path": "~/.ssh/id1_rsa",
            "path": "/path/to/remote/milex",
            "env_command": "source /path/to/remote/venv/bin/activate",
            "slurm_account": "your_slurm_account"
        }
    }
    ```
    If you have multiple slurm accounts on the same machine, then it would be best to create a second machine (say machine 2) with the same
    configuration as the previous machine except for the slurm_account field.

3. **Save and Exit**: After editing, save the file and exit the editor. The script will automatically update the configuration.

4. **Setup Directories and Environment**: The script will then create necessary directories on the specified paths and update `.bashrc` files for environment variable persistence.

## Creating an SSH Key

If you do not have an SSH key for accessing remote machines, you will need to create one.

### Steps to Create an SSH Key:

1. **Open a Terminal**: On your local machine, open a terminal.

2. **Generate SSH Key**: Run the following command and follow the on-screen instructions. Press Enter to accept default file locations and set a secure passphrase when prompted.

    ```bash
    ssh-keygen -t rsa -b 4096
    ```

3. **Locate SSH Public Key**: By default, the public key is saved in `~/.ssh/id_rsa.pub`.

### Linking the SSH Key to the Cluster:

1. **Copy Public Key**: Use the `ssh-copy-id` command to add your public key to the `authorized_keys` file on your remote machines.

    ```bash
    ssh-copy-id -i ~/.ssh/id_rsa.pub your_username@remote_hostname
    ```

2. **Enter Password**: You will be prompted to enter your password for the remote machine.

3. **Test SSH Connection**: Test your SSH connection to the remote machine. If set up correctly, it should not ask for your password (except for the passphrase of your key if you set one).

    ```bash
    ssh your_username@remote_hostname
    ```

By following these steps, you will have set up a secure SSH connection to your remote machines and configured Milex to use this connection for job execution.

