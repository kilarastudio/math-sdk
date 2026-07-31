# Setup and installation

***Running the math-sdk requires [uv](https://docs.astral.sh/uv/) and Python 3.12.***

***Rust/Cargo must also be installed for the optimization algorithm to run!***

Clone the Math SDK repository to get started
```sh
git@github.com:StakeEngine/math-sdk.git
```

## Installation

Assuming [uv](https://docs.astral.sh/uv/) is installed, set up the SDK with:
```sh
uv sync
```
This creates `.venv`, installs the locked dependencies from `uv.lock`, and installs the math-sdk in editable mode.

Once the relavent parameters are set for a particular game, execute the run.py file using:
```sh
  make run GAME=<game_id>
```


## Installing Cargo (Only if using Optimization Algorithm)

If the optimization algorithm is being utilized, [**Rust**](https://www.rust-lang.org/) and **Cargo** should be [installed](https://doc.rust-lang.org/cargo/getting-started/installation.html). 

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```


## Running Commands

Use `uv run` to execute commands in the managed environment without manually activating it:

```sh
uv run pytest tests/ -v
uv run python games/<game_id>/run.py
```

`make setup`, `make test`, and `make run GAME=<game_id>` remain available as shortcuts.
