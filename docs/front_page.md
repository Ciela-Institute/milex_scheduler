# Milex Scheduler

`milex-scheduler` is a package that simplifies the process of submitting
jobs on a SLURM hig performance cluster (HPC).
It provides an abstraction layer over the SLURM shell scripts,
so that you don't have to write them manually. It also handles job dependencies
using job names, so you don't have to grab job IDs from the output of `sbatch`.
In summary, `milex-scheduler` is an interface for

- Reproducible and automated job submission
- Bundling jobs into a single submission script
- Handling job dependencies
- Submitting jobs remotely

```{tableofcontents}

```
