# Stake Engine Math SDK

Welcome to [Stake Engine Math SDK](https://engine.stake.com/)!

The Math SDK is a Python-based engine for defining game rules, simulating outcomes, and optimizing win distributions. It generates all necessary backend and configuration files, lookup tables, and simulation results.
   

For technical details [view the docs](https://stakeengine.github.io/math-sdk/)


# Installation
 
This repository requires [uv](https://docs.astral.sh/uv/) and Python 3.12. uv manages the project Python environment and dependencies.
If the included optimization algorithm is being used, Rust/Cargo will also need to be installed.

Install dependencies and create the project environment with:
```sh
uv sync
```

Run tests with `uv run pytest tests/`, or use `make setup`, `make test`, and `make run GAME=<game_id>` as shortcuts for the equivalent uv commands.

Alternatively, visit our [Setup and Installation page](https://stakeengine.github.io/math-sdk/math_docs/general_overview/) for more details.
