# Milex Scheduler

`milex-scheduler` is a package that simplifies the process of scheduling and
running jobs on a SLURM cluster. It provides an abstraction layer over the SLURM
shell scripts and provides the following features:

- Reproducibility of job configurations
  - User-agnostic job scheduling
  - Job configurations saved in a human-readable format (JSON)
  - Automated Job scheduling and submission
- Bundling and submitting multiple jobs together with a single command
- Dependency between jobs managed using names instead of SLURM specific job IDs
- Submitting jobs remotely across SSH connections

```{tableofcontents}

```
