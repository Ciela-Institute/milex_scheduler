import os
from typing import Union
from collections import defaultdict
from .utils import load_config

__all__ = ["dependency_graph", "update_slurm_script_with_dependencies"]

def dependency_graph(jobs):
    """
    Build a dependency graph from a dictionary of jobs. 
    
    Exemple:
        jobs = {
            "JobA": {},
            "JobB": {"dependencies": ["JobA"]},
            "JobC": {"dependencies": ["JobA", "JobB"]},
        }
        dependency_graph(jobs) = {
                "JobA": ["JobB", "JobC"],
                "JobB": ["JobC"],
                "JobC": []
            }
    """
    dependency_graph = defaultdict(list)
    names = set()
    for task_name, job_details in jobs.items():
        if task_name in names:
            raise ValueError("Duplicate tasks: {}".format(task_name))
        names.add(task_name)
        dependency_graph[task_name] = []
        if job_details.get('dependencies') is not None: # avoid case where dependencies is None
            for dep in job_details.get('dependencies', []):
                dependency_graph[dep].append(task_name)
    return dependency_graph


def update_slurm_script_with_dependencies(script_name, dependency_job_ids: Union[list, tuple, int]):
    if not isinstance(dependency_job_ids, (list, tuple)):
        dependency_job_ids = [dependency_job_ids]
    user_config = load_config()
    file_path = os.path.join(user_config['local']['path'], 'slurm', script_name)
    
    with open(file_path, 'r') as file:
        lines = file.readlines()

    dependency_line_index = None
    for i, line in enumerate(lines):
        if line.startswith("#SBATCH --dependency"):
            dependency_line_index = i
            existing_deps = line.strip().split("afterok:")[-1]
            new_deps = ':'.join(dependency_job_ids)
            if existing_deps:
                new_deps = existing_deps + ':' + new_deps
            lines[i] = f"#SBATCH --dependency=afterok:{new_deps}\n"
            break

    if dependency_line_index is None:
        # Insert the dependency directive after the shebang line
        dependency_directive = f"#SBATCH --dependency=afterok:{':'.join(dependency_job_ids)}\n"
        for i, line in enumerate(lines):
            if line.startswith("#!/bin/bash"):
                lines.insert(i + 1, dependency_directive)
                break

    with open(file_path, 'w') as file:
        file.writelines(lines)

