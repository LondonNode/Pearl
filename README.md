[![pipeline status](https://github.com/LondonNode/Pearl/actions/workflows/ci.yaml/badge.svg)](https://github.com/LondonNode/Pearl/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/gh/LondonNode/Pearl/branch/main/graph/badge.svg?token=M3OUCWYAWM)](https://codecov.io/gh/LondonNode/Pearl)
[![codestyle](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<img src="docs/images/logo.jpg" align="right" width="50%"/>


# Pearl
The **P**arallel **E**volutionary **a**nd **R**einforcement **L**earning **L**ibrary (Pearl) is a pytorch based package with the goal of being excellent for rapid prototyping of new adaptive decision making algorithms in the intersection between reinforcement learning (RL) and evolutionary computation (EC). As such, this is **not** intended to provide template pre-built algorithms as a baseline, but rather flexible tools to allow the user to quickly build and test their own implementations and ideas. A [technical report](https://arxiv.org/abs/2201.09568) and separate [tutorial repo](https://github.com/LondonNode/Pearl-tutorials) using Google Collab are also included to introduce users to the library.

## Main Features
| **Features**                      | **Pearl** |
| ---------------------------       | ----------------------|
| Model Free RL algorithms (e.g. Actor Critic) | :heavy_check_mark: |
| Model Based RL algorithms (e.g. Dyna-Q) | :heavy_check_mark: |
| EC algorithms (e.g. Genetic Algorithm)   | :heavy_check_mark: |
| Hybrid algorithms (e.g. CEM-DDPG) | :heavy_check_mark: |
| Multi-agent suppport              | :heavy_check_mark: |
| Tensorboard integration           | :heavy_check_mark: |
| Modular and extensible components | :heavy_check_mark: |
| Opinionated module settings       | :heavy_check_mark: |
| Custom callbacks                  | :heavy_check_mark: |

## User Guide

### Installation
There are two options to install this package:
1. `pip install pearll`
2. `git clone git@github.com:LondonNode/Pearl.git`

### Module Guide
- `agents`: implementations of RL and EC agents where the other modular components are put together
- `buffers`: these handle storing and sampling of trajectories
- `callbacks`: inject logic for every step made in an environment (e.g. save model, early stopping)
- `common`: common methods applicable to all other modules (e.g. enumerations) and a main `utils.py` file with some useful general logic
- `explorers`: action explorers for enhanced exploration by adding noise to actions and random exploration for first n steps
- `models`: neural network structures which are structured as `encoder` -> `torso` -> `head`
- `signal_processing`: signal processing logic for extra modularity (e.g. TD returns, GAE)
- `updaters`: update neural networks and adaptive/iterative algorithms
- `settings.py`: settings objects for the above components, can be extended for custom components

### Agent Templates
See `pearll/agents/templates.py` for the templates to create your own agents! 
For more examples, see specific agent implementations under `pearll/agents`.

### Agent Performance
To see training performance, use the command `tensorboard --logdir runs` or `tensorboard --logdir <tensorboard_log_path>` defined in your algorithm class initialization.

### Python Scripts
To run these you'll need to go to wherever the library is installed, `cd pearll`.

- `demo.py`: script to run very basic demos of agents with pre-defined hyperparameters, run `python3 -m pearll.demo -h` for more info
- `plot.py`: script to plot more complex plots that can't be obtained via Tensorboard (e.g. multiple subplots), run `python3 -m pearll.plot -h` for more info

## Developer Guide
### Scripts
**Linux**
1. `scripts/setup_dev.sh`: setup your virtual environment
2. `scripts/run_tests.sh`: run tests

**Windows**
1. `scripts/windows_setup_dev.bat`: setup your virtual environment
2. `scripts/windows_run_tests.bat`: run tests

### Dependency Management
Pearl uses [poetry](https://python-poetry.org/docs/basic-usage/) for dependency management and build release instead of pip. As a quick guide:
1. Run `poetry add [package]` to add more package dependencies.
2. Poetry automatically handles the virtual environment used, check `pyproject.toml` for specifics on the virtual environment setup.
3. If you want to run something in the poetry virtual environment, add `poetry run` as a prefix to the command you want to execute. For example, to run a python file: `poetry run python3 script.py`.

## Credit

### Citing Pearl

```
@misc{tangri2022pearl,
      title={Pearl: Parallel Evolutionary and Reinforcement Learning Library}, 
      author={Rohan Tangri and Danilo P. Mandic and Anthony G. Constantinides},
      year={2022},
      eprint={2201.09568},
      archivePrefix={arXiv},
      primaryClass={cs.LG}
}
```

### Acknowledgements

Pearl was inspired by [Stable Baselines 3](https://github.com/DLR-RM/stable-baselines3) and [Tonic](https://github.com/fabiopardo/tonic)
