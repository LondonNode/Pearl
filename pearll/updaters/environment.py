from abc import ABC, abstractmethod
from typing import Iterator, Type

import torch as T

from pearll.common.type_aliases import Tensor, UpdaterLog
from pearll.models.actor_critics import Model


class BaseDeepUpdater(ABC):
    """
    Base class for updating a deep environment model.
    """

    def __init__(
        self,
        optimizer_class: Type[T.optim.Optimizer] = T.optim.Adam,
        max_grad: float = 0,
    ) -> None:
        self.optimizer_class = optimizer_class
        self.max_grad = max_grad

    def run_optimizer(
        self,
        optimizer: T.optim.Optimizer,
        loss: T.Tensor,
        model_parameters: Iterator[T.nn.Parameter],
    ) -> None:
        """Run an optimization step"""
        optimizer.zero_grad()
        loss.backward()
        if self.max_grad > 0:
            T.nn.utils.clip_grad_norm_(model_parameters, self.max_grad)
        optimizer.step()

    @abstractmethod
    def __call__(
        self,
        model: Model,
        observations: Tensor,
        actions: Tensor,
        targets: Tensor,
        learning_rate: float = 0.001,
    ) -> UpdaterLog:
        """Run an optimization step"""


class DeepRegression(BaseDeepUpdater):
    """
    Update a deep environment model using a deep regression algorithm.

    :param loss_class: The loss class to use e.g. MSE
    :param optimizer_class: the type of optimizer to use, defaults to Adam
    :param max_grad: maximum gradient clip value, defaults to no clipping with a value of 0
    """

    def __init__(
        self,
        loss_class: T.nn.Module = T.nn.MSELoss(),
        optimizer_class: Type[T.optim.Optimizer] = T.optim.Adam,
        max_grad: float = 0,
    ) -> None:
        super().__init__(optimizer_class, max_grad)
        self.loss_class = loss_class

    def __call__(
        self,
        model: Model,
        observations: Tensor,
        actions: Tensor,
        targets: Tensor,
        learning_rate: float = 0.001,
    ) -> UpdaterLog:
        """
        Run an optimization step

        :param model: The model to update (observation, reward or done models)
        :param observations: The observations as input to the model
        :param actions: The actions as input to the model
        :param targets: The targets to regress against
        :param learning_rate: The learning rate to use
        """
        params = model.parameters()
        optimizer = self.optimizer_class(params, lr=learning_rate)
        loss = self.loss_class(model(observations, actions), targets)
        self.run_optimizer(optimizer, loss, params)

        return UpdaterLog(loss=loss.detach().item())
