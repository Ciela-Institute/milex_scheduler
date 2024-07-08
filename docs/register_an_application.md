# Register a script

In order to schedule and submit your scripts, you will have to construct your
script with a specific structure. You will also need to register them in your
package's `pyproject.toml` file in order for `milex-schedule` to be able to be
able to run them.

## Script Structure

A script must be populated with 3 functions, namely `main()`, `parse_args()` and
`cli()`. The advantage of this structure is that `cli()`, a crucial function for
scheduling and running your script, will always be identical. This allows you to
copy paste `cli()` into all your scripts without modification.

Below, we detail the design principles of `main()`, `parse_args()`. `cli()` can
then be copied verbatim into your script.

### `main`

The `main()` function serves as the entry point of your application. Typically,
it will start as follows:

```python
def main():
    # Imports

    args = parse_args()

    # Application logic goes here
```

It is recommended to import all the necessary packages inside the `main`
function to avoid slow scheduling of jobs, especially if you have heavy imports
like Pytorch.

### `parse_args`

The `parse_args()` function is used to parse the command-line arguments. For
example

```python
def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Your application description here.")
    # Define your arguments here
    parser.add_argument("--example", type=str, help="Example argument")
    args = parser.parse_args()
    return args
```

### `cli()`

If you are using the `parse_args()` function, you can include this `cli()`
function verbatim in your script

```python
def cli():
    import sys, json

    args = parse_args()
    print(json.dumps(vars(args), indent=4))
    sys.exit(0)
```

## Register your Script

In order to schedule a script, both the `main()` and the `cli()` functions must
be registered inside your environment as applications. In this section, we
detail the steps necessary to achieve this, starting from the creation of a
package in case your project is yet a package.

### Create a Package

To create a package, you can follow the instructions in the
[Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
to create a package.

Alternatively, you can adopt the following basic structure for a
`pyproject.toml` file.

```toml
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "name_of_package"
version = "0.1.0"
description = "A short description of my package"
authors = [
    {name="My Name", email="my_name@example.com"},
    ]
requires-python = ">=3.8"
```

The `pyproject.toml` file must be saved in the root of your project

```
my_package/
├── pyproject.toml
├── src/
│   └── name_of_package/
│       ├── __init__.py
│       └── script.py
└── README.md
```

Once this file is created, you can install your package in your environment
using the following command (from the root of your project)

```shell
pip install -e .
```

This creates an editable installation of your package in your environment, which
means that any changes you make to the package will be reflected in your
environment.

### Register the Script in `pyproject.toml`

Assuming that your script is in `my_package/src/name_of_package/script.py` and
has the structure described above, you can register it in the `pyproject.toml`
file by adding the following lines

```toml
[project.scripts]
my-script     = "name_of_package.script:main"
my-script-cli = "name_of_package.script:cli"
```

Both `my-script` and `my-script-cli` must be registered in the `pyproject.toml`
file for `milex-schedule` to be able to run your script.

Once your script is registered, it can be scheduled and run using the
`milex-schedule` and `milex-submit` commands. More information on these commands
can be found in the [Getting Started](./getting_started.md) section.
