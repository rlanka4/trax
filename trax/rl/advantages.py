# coding=utf-8
# Copyright 2020 The Trax Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""RL advantage estimators."""

import gin
import numpy as np


common_args = ['rewards', 'returns', 'values', 'gamma', 'n_extra_steps']


@gin.configurable(blacklist=common_args)
def monte_carlo(rewards, returns, values, gamma, n_extra_steps):
  """Calculate Monte Carlo advantage.

  We assume the values are a tensor of shape [batch_size, length] and this
  is the same shape as rewards and returns.

  Args:
    rewards: the rewards, tensor of shape [batch_size, length]
    returns: discounted returns, tensor of shape [batch_size, length]
    values: the value function computed for this trajectory (shape as above)
    gamma: float, gamma parameter for TD from the underlying task
    n_extra_steps: number of extra steps in the sequence

  Returns:
    the advantages, a tensor of shape [batch_size, length - n_extra_steps].
  """
  del rewards
  del gamma
  (_, length) = returns.shape
  return (returns - values)[:, :(length - n_extra_steps)]


@gin.configurable(blacklist=common_args)
def td_k(rewards, returns, values, gamma, n_extra_steps):
  """Calculate TD-k advantage.

  The k parameter is assumed to be the same as n_extra_steps.

  We calculate advantage(s_i) as:

    gamma^n_steps * value(s_{i + n_steps}) - value(s_i) + discounted_rewards

  where discounted_rewards is the sum of rewards in these steps with
  discounting by powers of gamma.

  Args:
    rewards: the rewards, tensor of shape [batch_size, length]
    returns: discounted returns, tensor of shape [batch_size, length]
    values: the value function computed for this trajectory (shape as above)
    gamma: float, gamma parameter for TD from the underlying task
    n_extra_steps: number of extra steps in the sequence, also controls the
      number of steps k

  Returns:
    the advantages, a tensor of shape [batch_size, length - n_extra_steps].
  """
  del returns
  # Here we calculate advantage with TD-k, where k=n_extra_steps.
  k = n_extra_steps
  assert k > 0
  advantages = (gamma ** k) * values[:, k:] - values[:, :-k]
  discount = 1.0
  for i in range(n_extra_steps):
    advantages += gamma * rewards[:, i:-(n_extra_steps - i)]
    discount *= gamma
  return advantages


@gin.configurable(blacklist=common_args)
def td_lambda(rewards, returns, values, gamma, n_extra_steps, lambda_=0.95):
  """Calculate TD-lambda advantage.

  The estimated return is an exponentially-weighted average of different TD-k
  returns.

  Args:
    rewards: the rewards, tensor of shape [batch_size, length]
    returns: discounted returns, tensor of shape [batch_size, length]
    values: the value function computed for this trajectory (shape as above)
    gamma: float, gamma parameter for TD from the underlying task
    n_extra_steps: number of extra steps in the sequence
    lambda_: discount parameter of the exponentially-weighted average

  Returns:
    the advantages, a tensor of shape [batch_size, length - n_extra_steps].
  """
  td_returns = np.zeros_like(returns)
  (_, length) = returns.shape
  td_returns[:, -1] = values[:, -1]
  for i in reversed(range(length - 1)):
    td_returns[:, i] = rewards[:, i] + gamma * (
        (1 - lambda_) * values[:, i + 1] + lambda_ * td_returns[:, i + 1]
    )
  return (td_returns - values)[:, :(returns.shape[1] - n_extra_steps)]
