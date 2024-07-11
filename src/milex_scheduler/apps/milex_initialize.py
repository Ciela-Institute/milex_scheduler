import argparse
from ..save_load_jobs import save_bundle


def parse_args():
    # fmt: off
    parser = argparse.ArgumentParser(description='Initialize a bundle of jobs to run with SLURM')
    parser.add_argument('bundle', help='Name of the job bundle (JSON file containing multiple jobs/scripts to be scheduled).')
    # fmt: on
    args = parser.parse_args()
    return args


def cli():
    import sys
    import json

    args, script_args = parse_args()
    if script_args is None:
        sys.exit(1)
    print(json.dumps(vars(args), indent=4))
    sys.exit(0)


def main():
    args = parse_args()
    save_bundle({}, args.bundle)
