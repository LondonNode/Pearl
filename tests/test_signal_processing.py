import gym
import numpy as np
import pytest
import torch as T

from pearll.common.utils import to_torch
from pearll.signal_processing.advantage_estimators import generalized_advantage_estimate
from pearll.signal_processing.crossover_operators import (
    fit_gaussian,
    one_point_crossover,
)
from pearll.signal_processing.mutation_operators import (
    gaussian_mutation,
    uniform_mutation,
)
from pearll.signal_processing.return_estimators import TD_lambda, TD_zero, soft_q_target
from pearll.signal_processing.sample_estimators import (
    sample_forward_kl_divergence,
    sample_reverse_kl_divergence,
)
from pearll.signal_processing.selection_operators import (
    naive_selection,
    roulette_selection,
    tournament_selection,
)


@pytest.mark.parametrize(
    "kl_divergence", [sample_forward_kl_divergence, sample_reverse_kl_divergence]
)
@pytest.mark.parametrize("dtype", ["torch", "numpy"])
def test_kl_divergence(kl_divergence, dtype):
    # KL Div = E(unbiased approx KL Div)
    T.manual_seed(8)
    num_samples = int(2e6)
    dist1 = T.distributions.Normal(0, 1)
    dist2 = T.distributions.Normal(1, 2)

    samples = dist2.sample((num_samples,))

    log_probs1 = dist1.log_prob(samples)
    log_probs2 = dist2.log_prob(samples)

    if kl_divergence == sample_forward_kl_divergence:
        full_kl_div = T.distributions.kl_divergence(dist1, dist2)
    else:
        full_kl_div = T.distributions.kl_divergence(dist2, dist1)

    approx_kl_div = to_torch(kl_divergence(log_probs1.exp(), log_probs2.exp(), dtype))
    mean_approx_kl_div = T.mean(approx_kl_div)

    assert T.allclose(full_kl_div, mean_approx_kl_div, rtol=5e-3)


def test_TD_lambda():
    rewards = T.ones(size=(2, 3))
    last_values = T.ones(size=(2,))
    last_dones = T.zeros(size=(2,))

    actual_returns = TD_lambda(rewards, last_values, last_dones, gamma=1)
    expected_returns = T.tensor([4, 4], dtype=T.float32)

    T.equal(actual_returns, expected_returns)


def test_TD_zero():
    rewards = T.ones(size=(3,))
    next_values = T.ones(size=(3,))
    dones = T.zeros(size=(3,))

    actual_returns = TD_zero(rewards, next_values, dones, gamma=1)
    expected_returns = T.tensor([2, 2, 2], dtype=T.float32)

    T.equal(actual_returns, expected_returns)


def test_generalized_advantage_estimate():
    rewards = T.ones(size=(3,))
    old_values = T.ones(size=(3,))
    new_values = T.ones(size=(3,))
    dones = T.zeros(size=(3,))

    actual_advantages, actual_returns = generalized_advantage_estimate(
        rewards, old_values, new_values, dones, gamma=1, gae_lambda=1
    )
    expected_advantages, expected_returns = (
        T.tensor([3, 2, 1], dtype=T.float32),
        T.tensor([4, 3, 2], dtype=T.float32),
    )

    T.equal(actual_advantages, expected_advantages)
    T.equal(actual_returns, expected_returns)


def test_soft_q_target():
    rewards = T.ones(size=(3,))
    dones = T.zeros(size=(3,))
    q_values = T.ones(size=(3,))
    log_probs = T.tensor([-1, -1, -1], dtype=T.float32)

    actual_target = soft_q_target(rewards, dones, q_values, log_probs, 1, 1)
    expected_target = T.tensor([3, 3, 3], dtype=T.float32)

    T.equal(actual_target, expected_target)


def test_naive_selection():
    population = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    fitness = np.array([2, 1, 3])
    actual_population = naive_selection(population, fitness)
    expected_population = np.array([[7, 8, 9]])
    np.testing.assert_array_equal(actual_population, expected_population)

    population = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
    fitness = np.array([2, 1, 3, 4])
    actual_population = naive_selection(population, fitness, ratio=0.8)
    expected_population = np.array([[1, 2, 3], [7, 8, 9], [10, 11, 12]])
    np.testing.assert_array_equal(actual_population, expected_population)

    population = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])
    fitness = np.array([1, 1, 1, 1])
    actual_population = naive_selection(population, fitness, ratio=0.75)
    expected_population = np.array([[4, 5, 6], [7, 8, 9], [10, 11, 12]])
    np.testing.assert_array_equal(actual_population, expected_population)


def test_tournament_selection():
    np.random.seed(8)
    population = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    fitness = np.array([2, 1, 3])
    actual_population = tournament_selection(population, fitness, 2)
    expected_population = np.array([[1, 2, 3], [7, 8, 9], [7, 8, 9]])

    np.testing.assert_array_equal(actual_population, expected_population)


def test_roulette_selection():
    np.random.seed(8)
    population = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    fitness = np.array([2, 1, 3])
    actual_population = roulette_selection(population, fitness)
    expected_population = np.array([[7, 8, 9], [7, 8, 9], [7, 8, 9]])

    np.testing.assert_array_equal(actual_population, expected_population)


def test_fit_gaussian():
    np.random.seed(9)
    parents = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    actual_population = fit_gaussian(parents, population_shape=(6, 3))
    expected_population = np.array(
        [
            [4.00271539, 4.29076477, 3.26620704],
            [3.96844382, 4.07320747, 4.82146386],
            [0.28331284, 3.79761412, 5.41045539],
            [2.41285934, 6.55760868, 10.26239949],
            [4.72672005, 6.73302296, 10.46496851],
            [5.05516432, 8.77890039, 3.79369273],
        ]
    )
    assert actual_population.shape == (6, 3)
    np.testing.assert_array_almost_equal(actual_population, expected_population)


def test_one_point_crossover():
    np.random.seed(8)
    population = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    actual_population = one_point_crossover(population, 1)
    expected_population = np.array([[1, 5, 6], [4, 2, 3], [7, 8, 9]])
    np.testing.assert_array_equal(actual_population, expected_population)

    actual_population = one_point_crossover(population)
    expected_population = np.array([[4, 5, 6], [1, 2, 3], [7, 8, 9]])
    np.testing.assert_array_equal(actual_population, expected_population)


def test_gaussian_mutation():
    np.random.seed(8)
    action_space = gym.spaces.Box(low=-1, high=1, shape=(3,))
    population = np.full((3, 3), 1, dtype=np.float32)

    actual_population = gaussian_mutation(population, action_space, mutation_rate=1)
    expected_population = np.array(
        [[1, 0.86956686, 0.6101016], [1, 1, 1], [0.6839435, 0.3276471, 0.84406894]]
    )
    np.testing.assert_array_almost_equal(actual_population, expected_population)

    actual_population = gaussian_mutation(population, action_space, mutation_rate=0)
    expected_population = population
    np.testing.assert_array_almost_equal(actual_population, expected_population)


def test_discrete_gaussian_mutation():
    action_space = gym.spaces.Discrete(5)
    population = np.full((3, 1), 1, dtype=np.int32)

    actual_population = gaussian_mutation(population, action_space, mutation_rate=1)
    expected_population = np.array([[1], [0], [2]])
    assert np.issubdtype(actual_population.dtype, np.integer)
    np.testing.assert_array_almost_equal(actual_population, expected_population)


def test_uniform_mutation():
    np.random.seed(8)
    action_space = gym.spaces.Box(low=-1, high=1, shape=(3,))
    population = np.full((3, 3), 1, dtype=np.float32)

    actual_population = uniform_mutation(population, action_space, mutation_rate=1)
    expected_population = np.array(
        [[0.80385023, 1, 1], [0.8447016, 1, 1], [0.47887915, 0.75503397, 1]]
    )
    np.testing.assert_array_almost_equal(actual_population, expected_population)

    actual_population = uniform_mutation(population, action_space, mutation_rate=0)
    expected_population = population
    np.testing.assert_array_almost_equal(actual_population, expected_population)


def test_discrete_uniform_mutation():
    action_space = gym.spaces.Discrete(5)
    population = np.full((3, 1), 1, dtype=np.int32)

    actual_population = uniform_mutation(population, action_space, mutation_rate=1)
    expected_population = np.array([[2], [0], [1]])
    assert np.issubdtype(actual_population.dtype, np.integer)
    np.testing.assert_array_almost_equal(actual_population, expected_population)
