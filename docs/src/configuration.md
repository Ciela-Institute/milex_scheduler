# Configuration

This document provides detailed instructions for the `milex-configuration`
command. This step abstracts away user specific information like

- SLURM account information (e.g. `def-bengioy`)
- Virtual environment activation commands (e.g.
  `source /path/to/remote/venv/bin/activate`)
- SSH credentials for remote machines

This document includes steps for creating an SSH key to securely access remote
machines in the section [Creating an SSH Key](ssh). To get started with the
configuration, run this command in a command-line interface:

```bash
milex-configuration
```

## `milex-configuration`

`milex-configuration` is a shortcut to modify the configuration file
`.milexconfig` saved in the user's home directory. When executed for the first
time, it will create the configuration file if it does not exist, and you will
be presented with the following file template

```json
{
  "local": {
    "path": "/path/to/local/milex",
    "env_command": "source /path/to/local/venv/bin/activate",
    "slurm_account": "def-bengioy"
  },
  "remote_machine": {
    "path": "/path/to/remote/milex",
    "env_command": "source /path/to/remote/venv/bin/activate",
    "slurm_account": "rrg-account_name",
    "hostname": "machine",
    "hosturl": "machine.domain.com",
    "username": "user1",
    "key_path": "~/.ssh/id_rsa"
  }
}
```

In what follows, we will explain the different fields in the configuration file.

### Local machine

`local` is the name of the machine where you are currently running the
`milex-configuration` command. It must always be present in the configuration
file.

#### `path`

This field specifies the absolute path to a directory where scripts, jobs, and
various other things will be stored for reproducibility. Once the configuration
is complete, the following directory structure will be created automatically

```
├── jobs
│   ├── *job_name*_*date*.json
├── slurm
│   ├── *script_name*_*date*.sh
├── models
├── results
└── data
```

Only the directories are created by `milex-configuration`. As you schedule jobs,
the `jobs` directory will be populated with JSON files containing job
information, and the `slurm` directory will be populated with SLURM shell
scripts.

**Notes**:

- The `*date*` is a timestamp automatically generated when a job is scheduled.
  The format is `YYYYmmDDHHMMSS`.
- In case multiple unique jobs are created simultaneously, timestamps are set
  one second in the future of each other to ensure uniqueness.

#### `env_command`

This field is used to activate your Python virtual environment before running
your jobs. If you are using `virtualenv`, the command will look like this:

```bash
source /path/to/venv/bin/activate
```

If you use `conda`, the command will look like this:

```bash
conda activate myenv
```

When SLURM shell script are automatically generated, the virtual environment is
activated before running the job. Here is an example of an generated SLURM shell
script:

```bash
#!/bin/bash
# SBATCH ...

# Activate the virtual environment
source /path/to/venv/bin/activate # Content of the `env_command` field

# Run the job
python my_script
```

#### `slurm_account`

This field specifies the SLURM account to use for job submission. Note that each
machine receives a unique SLURM account. If you have multiple SLURM accounts on
the same machine, you can create a new machine in the configuration file

```json
{
  "local": {
    "path": "/path/to/local/milex",
    "env_command": "source /path/to/local/venv/bin/activate",
    "slurm_account": "def-bengioy"
  },
  "local_rrg": {
    "path": "/path/to/local/milex",
    "env_command": "source /path/to/local/venv/bin/activate",
    "slurm_account": "rrg-bengioy"
  }
}
```

### Remote machine

The `remote_machine` field is optional and is used to specify the configuration
details for a remote machine, which can be accessed via SSH protocols. If you
don't need this, you can remove the `remote_machine` field from the
configuration file. **Notes**:

- The `path` field must be an absolute path with respect to the remote machine.

#### `hostname`

This field specifies the hostname of a remote machine from the `~/.ssh/config`
file. For more details on how to create an SSH config file, see the section
[Create an SSH config file](config).

**Note**: This is the preferable way to specify the hostname of the remote
machine. If provided, the other fields `hosturl`, `username`, and `key_path` are
not required.

#### `username`

This field specifies your username on the remote machine. For example, `user1`.

#### `hosturl`

This field specifies the URL of the remote machine. For example,
`machine.domain.com`.

#### `key_path`

This field specifies the path to your SSH private key. For example,
`~/.ssh/id_rsa`. See the section [Creating an SSH Key](ssh) for instructions on
how to create an SSH key.

(ssh)=

## Create an SSH Key

If you do not have an SSH key for accessing remote machines, you will need to
create one. In what follows, we details some of the steps to do so.

### Generate an SSH Key

You can typically generate an SSH key using the `ssh-keygen` command. For
example

```bash
ssh-keygen -t rsa -b 4096 "your_email@example.com"
```

You can find more information about the `ssh-keygen` command by running
`man ssh-keygen` or visiting
[this GitHub instruction page](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
for a walkthrough of the process.

The key will be saved in the `~/.ssh` directory by default. If you chose the
name `id_rsa` for the key, the private key will be saved in `~/.ssh/id_rsa` and
the public key in `~/.ssh/id_rsa.pub`.

### Link an SSH Key to the remote machine

Use the `ssh-copy-id` command to add your public key to the `authorized_keys`
file on your remote machines.

```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub username@hostname
```

`username` is your username on the remote machine and `hostname` is the hostname
or IP address of the remote machine. With this setup, you should be able to
connect to the remote machine without being prompted for a password.

```bash
ssh username@hostname
```

(config)=

## Create an SSH config file (recommended)

To simplify the SSH connection process even more, you can create an SSH config
file at `~/.ssh/config` with the following content

```bash
Host remote_machine
    HostName hostname
    User username
    IdentityFile ~/.ssh/id_rsa
```

With this, you can connect to the remote machine using the following command

```bash
ssh remote_machine
```

Similarly, you will only need to specify the `hostname` in your
`milex-configuration` to connect to the remote machine.

### Dealing with 2FA authentication

In case a 2FA protocol is enabled on the remote machine, you can add persistence
to the ssh-agent to avoid prompting the 2FA authentication process every time
you connect to the remote machine. Here is how you can modify the
`~/.ssh/config` file

```bash
Host remote_machine
    HostName hostname
    User username
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 60
    ControlMaster auto
    ControlPersist yes
    ControlPath ~/.ssh/sockets/%r@%h-%p
```

`ServerAliveInterval 60` will send a keep-alive signal to the server every 60
seconds to keep the connection alive, keeping the connection open for a longer
period of time. The `ControlMaster` and `ControlPersist` options are used to
multiplex SSH connections, meaning that you can open multiple SSH sessions to
the same server without having to re-authenticate each time.

This configuration is **highly recommended** for remote machines that require
2FA authentication. Especially if you plan submitting large bundles of jobs on
the remote machine and don't want to be bothered every time
`milex-configuration` opens a new SSH connection to the remote machine.
