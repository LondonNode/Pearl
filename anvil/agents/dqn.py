from typing import List, Optional, Type, Union

import numpy as np
import torch as T
from gym import Env

from anvil.agents.base_agent import BaseAgent
from anvil.buffers.base_buffer import BaseBuffer
from anvil.buffers.replay_buffer import ReplayBuffer
from anvil.callbacks.base_callback import BaseCallback
from anvil.common.type_aliases import ExplorerSettings, Log, OptimizerSettings
from anvil.common.utils import get_space_shape, torch_to_numpy
from anvil.explorers.base_explorer import BaseExplorer
from anvil.models.actor_critics import (
    ActorCritic,
    ActorCriticWithCriticTarget,
    Critic,
    EpsilonGreedyActor,
)
from anvil.models.encoders import IdentityEncoder
from anvil.models.heads import DiscreteQHead
from anvil.models.torsos import MLP
from anvil.models.utils import get_mlp_size
from anvil.signal_processing.sample_estimators import TD_zero
from anvil.updaters.critics import BaseCriticUpdater, QRegression


def get_default_model(env: Env):
    observation_shape = get_space_shape(env.observation_space)
    action_size = env.action_space.n
    observation_size = get_mlp_size(observation_shape)

    encoder = IdentityEncoder()
    torso = MLP(layer_sizes=[observation_size, 16, 16], activation_fn=T.nn.ReLU)
    head = DiscreteQHead(input_shape=16, output_shape=action_size)

    actor = EpsilonGreedyActor(
        critic_encoder=encoder, critic_torso=torso, critic_head=head
    )
    critic = Critic(encoder=encoder, torso=torso, head=head)

    return ActorCriticWithCriticTarget(actor, critic)


class DQN(BaseAgent):
    def __init__(
        self,
        env: Env,
        model: ActorCritic,
        updater_class: Type[BaseCriticUpdater] = QRegression,
        optimizer_settings: OptimizerSettings = OptimizerSettings(),
        buffer_class: Type[BaseBuffer] = ReplayBuffer,
        buffer_size: int = int(1e6),
        action_explorer_class: Type[BaseExplorer] = BaseExplorer,
        explorer_settings: ExplorerSettings = ExplorerSettings(start_steps=0),
        callbacks: Optional[List[Type[BaseCallback]]] = None,
        device: Union[T.device, str] = "auto",
        verbose: bool = True,
        render: bool = False,
        model_path: Optional[str] = None,
        tensorboard_log_path: Optional[str] = None,
        log_level: str = "",
        n_envs: int = 1,
    ) -> None:
        model = model or get_default_model(env)
        super().__init__(
            env,
            model,
            buffer_class,
            buffer_size,
            callbacks=callbacks,
            device=device,
            verbose=verbose,
            model_path=model_path,
            tensorboard_log_path=tensorboard_log_path,
            log_level=log_level,
            n_envs=n_envs,
            render=render,
        )

        self.updater = updater_class(
            optimizer_class=optimizer_settings.optimizer_class,
            lr=optimizer_settings.learning_rate,
            max_grad=optimizer_settings.max_grad,
        )

        if explorer_settings.scale is not None:
            self.action_explorer = action_explorer_class(
                action_space=env.action_space,
                start_steps=explorer_settings.start_steps,
                scale=explorer_settings.scale,
            )
        else:
            self.action_explorer = action_explorer_class(
                action_space=env.action_space, start_steps=explorer_settings.start_steps
            )

    def _fit(
        self, batch_size: int, actor_epochs: int = 1, critic_epochs: int = 1
    ) -> Log:
        critic_losses = np.zeros(shape=(critic_epochs))
        for i in range(critic_epochs):
            trajectories = self.buffer.sample(batch_size=batch_size)

            with T.no_grad():
                next_q_values = self.model.target_critic(trajectories.next_observations)
                next_q_values, _ = next_q_values.max(dim=-1)
                next_q_values = torch_to_numpy(next_q_values.reshape(-1, 1))
                next_q_values = np.expand_dims(next_q_values, axis=-1)
                target_q_values = TD_zero(
                    trajectories.rewards, next_q_values, trajectories.dones
                )

            updater_log = self.updater(
                self.model,
                trajectories.observations,
                target_q_values,
                actions_index=trajectories.actions,
            )
            critic_losses[i] = updater_log.loss

        self.model.assign_targets()

        return Log(critic_loss=np.mean(critic_losses))