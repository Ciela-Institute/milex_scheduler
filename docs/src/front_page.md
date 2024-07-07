# Milex Scheduler

`milex-scheduler` is a package that simplifies the process of scheduling and
running jobs on a SLURM cluster. It provides an abstraction layer over the SLURM
shell scripts focused on the following key features:

- Schedule multiple jobs at once
  - With dependencies (only by specifying job names in the dependency)
  - Or by appending to the same script (e.g. nesting jobs with similar
    configurations in a **for** loop)
- Submitting jobs on different machines across SSH connections
- Reproducibility of job configurations
  - Each job or bundle of jobs is saved as a JSON file with a unique timestamps
  - SLURM shell script(s) are automatically generated (and submitted) from these
    JSON files
  - User-agnostic job scheduling

```{tableofcontents}

```
