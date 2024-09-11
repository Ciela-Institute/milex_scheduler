# Getting started

## Installation

### Install the `milex-scheduler` package

```bash
git clone git@github.com:Ciela-Institute/milex_scheduler.git
cd milex_scheduler
pip install -e .
```

### Configure `milex-scheduler` for your environment

```bash
milex-configuration
```

This command will allow you to configure paths and user-specific details for
your local and remote SLURM machines. More details can be found in the
[Configuration](configuration.md) section.

### Register your application in the `pyproject.toml` file of your package

```toml
[project.scripts]
my-script = "my_package.module:main"
my-script-cli = "my_package.module:cli"
```

More details can be found in the [Register a script](register_a_script.md)
section.

## Basic Usage

### Schedule a job

```bash
milex-schedule my-script \
    # Application args
    --my_job_arg1=arg1 \
    # SLURM args
    --time=00-01:00 \
    --cpus_per_task=1 \
    --gres=gpu:1 \
    --mem=16G
```

This command schedules `my-script` to run for 1 hour, using 1 CPU, 1 GPU, and
16GB of memory.

### Submit a job

Once the job is scheduled, you can submit it at any time just by using the name
of the application.

```bash
milex-submit my-script --machine=machine
```

This command submits `my-script` on the `machine` name specified in your
configuration (see [Milex Configuration](#Milex-Configuration)). You can also
schedule and submit a job at the same time to skip a step.

```bash
milex-schedule my-script --submit --machine=machine\
    # Application and SLURM args
    ...
```

### Schedule multiple jobs

Use the `--append` keyword to combine multiple jobs in a bundle. Use the
`--name` keyword to specify the name of the bundle.

```bash
milex-schedule job1 --name=my-bundle
milex-schedule job2 --append --name=my-bundle
milex-submit my-bundle
```

An empty bundle can be initialized as follows
```bash
milex-initialize my-bundle
```
Jobs can then be appended to this bundle using `milex-schedule --append --name=my-bundle`.
This is useful when you want to schedule jobs in a loop.

**Warning**: In case `--append` is not used, two bundles (each with a single job) are
created with unique timestamps. Only the last bundle created is submitted.


### Schedule jobs with dependencies

Dependencies can be set by specifying the job names in the `--dependencies`
argument.

```bash
milex-schedule job1 --name=my-bundle
milex-schedule job2 --append --name=my-bundle --dependencies job1
```

Multiple dependencies can be set by separating the job names with a space.

```bash
milex-schedule job3 --append --name=my-bundle \
    --dependencies job1 job2
```

<!--The `--dependency_type` argument specifies the type of dependency. The default-->
<!--is `afterany`.-->

**Notes**:

- Any dependency loop will be detected and raise an error (e.g. if job1 depends
  on job2 and vice versa).
- Order in which jobs are appended is not important. Jobs are sorted in
  topological order before submission.
  <!--- `--dependency_type` can be a list of same length as `--dependencies` or a-->
    <!--single value to be broadcasted.-->


### Pre-commands

Commands like copying files or creating directories can be
executed before the python script by using the `--pre-command` argument when scheduling a job.

```bash
milex-schedule my-script \
    --pre-command "mkdir -p /path/to/my/directory"
    ...
```
Multiple pre-commands are provided by separating them with a semicolon

```bash
milex-schedule my-script \
    --pre-command "mkdir -p /path/to/my/directory; cp /path/to/my/file /path/to/my/directory"
    ...
```

Or separating them with a space

```bash
milex-schedule my-script \
    --pre-command \
    "mkdir -p /path/to/my/directory" \
    "cp /path/to/my/file /path/to/my/directory"\
    ...
```
