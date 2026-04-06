"""
RLlib PPO training script with action masking and self-play for TTR Europe.

All players share one policy ("shared_policy") — parameter sharing self-play.
Action masking is applied via RLlib's built-in ActionMaskingTorchRLModule,
which reads the "action_mask" key from the observation dict and sets invalid
action logits to −∞ so they are never sampled.

Usage:
    # Quick smoke test (< 5 min, verifies the stack works end-to-end)
    python -m ttr_game.agents.train --test

    # Train on the base game only
    python -m ttr_game.agents.train --num-players 4 --num-iters 500

    # Train on a single expansion
    python -m ttr_game.agents.train --num-players 4 --expansion 1912 --num-iters 500

    # Train on ALL expansions simultaneously (randomly sampled per episode)
    python -m ttr_game.agents.train --num-players 4 --all-expansions --num-iters 500

    # Evaluate a saved checkpoint
    python -m ttr_game.agents.train --eval ./checkpoints/<checkpoint_dir>

Requirements:
    pip install "ray[rllib]" torch pettingzoo gymnasium supersuit
"""
from __future__ import annotations
import argparse
import os
from typing import List, Optional

import ray
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.core.rl_module.rl_module import RLModuleSpec
from ray.rllib.examples.rl_modules.classes.action_masking_rlm import (
    ActionMaskingTorchRLModule,
)


# ---------------------------------------------------------------------------
# Config builder
# ---------------------------------------------------------------------------

def build_config(
    num_players: int,
    num_env_runners: int = 4,
    train_batch_size: int = 4096,
    minibatch_size: int = 256,
    num_epochs: int = 10,
    num_gpus: int = 0,
    seed: Optional[int] = None,
    expansion: Optional[str] = None,
    expansions: Optional[List[str]] = None,
) -> PPOConfig:
    """
    Return a ready-to-build PPOConfig for TTR Europe self-play.

    Pass `expansion` to train on a single variant, or `expansions` (a list) to
    train on multiple variants with one randomly sampled per episode.
    Omitting both defaults to the base game.
    """
    from ..env.ttr_env import TTRMultiAgentEnv

    env_config: dict = {"num_players": num_players}
    if seed is not None:
        env_config["seed"] = seed
    if expansions is not None:
        env_config["expansions"] = expansions
    elif expansion is not None:
        env_config["expansion"] = expansion

    cfg = (
        PPOConfig()
        .environment(
            env=TTRMultiAgentEnv,
            env_config=env_config,
        )
        .framework("torch")
        .env_runners(num_env_runners=num_env_runners)
        .learners(num_learners=0, num_gpus_per_learner=num_gpus)
        .training(
            lr=3e-4,
            gamma=0.99,
            lambda_=0.95,
            clip_param=0.2,
            vf_clip_param=10.0,
            entropy_coeff=0.01,
        )
        .rl_module(
            rl_module_spec=RLModuleSpec(module_class=ActionMaskingTorchRLModule),
        )
        .multi_agent(
            policies={"shared_policy"},
            policy_mapping_fn=lambda agent_id, *args, **kwargs: "shared_policy",
            policies_to_train=["shared_policy"],
        )
    )
    cfg.train_batch_size_per_learner = train_batch_size
    cfg.minibatch_size = minibatch_size
    cfg.num_epochs = num_epochs
    return cfg


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(
    num_players: int = 4,
    num_iters: int = 500,
    checkpoint_freq: int = 50,
    checkpoint_dir: str = "./checkpoints",
    num_env_runners: int = 4,
    num_gpus: int = 0,
    expansion: Optional[str] = None,
    expansions: Optional[List[str]] = None,
) -> None:
    """Run PPO self-play training and save checkpoints periodically."""
    ray.init(ignore_reinit_error=True)
    checkpoint_dir = os.path.abspath(checkpoint_dir)
    os.makedirs(checkpoint_dir, exist_ok=True)

    cfg = build_config(
        num_players=num_players,
        num_env_runners=num_env_runners,
        num_gpus=num_gpus,
        expansion=expansion,
        expansions=expansions,
    )
    algo = cfg.build_algo()

    variant_label = (
        f"all {len(expansions)} expansions" if expansions is not None
        else (expansion or "base")
    )
    print(f"PPO self-play | {num_players} players | {num_iters} iters | variant={variant_label}")

    for i in range(1, num_iters + 1):
        result = algo.train()
        mean_r = result.get("env_runners", {}).get("episode_return_mean",
                 result.get("episode_return_mean", float("nan")))
        eps    = result.get("env_runners", {}).get("num_episodes",
                 result.get("num_episodes", "?"))
        print(f"  iter {i:4d}  reward_mean={mean_r:+.1f}  episodes={eps}")

        if i % checkpoint_freq == 0:
            path = algo.save(checkpoint_dir)
            print(f"  → checkpoint saved: {path}")

    final = algo.save(checkpoint_dir)
    print(f"\nTraining complete. Final checkpoint: {final}")
    ray.shutdown()


# ---------------------------------------------------------------------------
# Quick smoke test  (--test flag)
# ---------------------------------------------------------------------------

def run_test() -> None:
    """
    Minimal training run that completes in under 5 minutes.
    Uses 2 players, 0 remote workers, tiny batches, and 5 iterations.
    Purpose: verify the full stack (env → RLModule → training loop) works
    before launching a full run on another machine.
    """
    print("=" * 62)
    print("  TTR Europe — RL stack smoke test")
    print("  2 players · 5 iterations · local mode (no remote workers)")
    print("=" * 62)

    ray.init(ignore_reinit_error=True, num_cpus=2)

    from ..env.ttr_env import TTRMultiAgentEnv

    cfg = (
        PPOConfig()
        .environment(
            env=TTRMultiAgentEnv,
            env_config={"num_players": 2, "seed": 42},
        )
        .framework("torch")
        .env_runners(num_env_runners=0)
        .learners(num_learners=0)
        .training(
            lr=3e-4,
            gamma=0.99,
            clip_param=0.2,
            entropy_coeff=0.01,
        )
        .rl_module(
            rl_module_spec=RLModuleSpec(module_class=ActionMaskingTorchRLModule),
        )
        .multi_agent(
            policies={"shared_policy"},
            policy_mapping_fn=lambda agent_id, *args, **kwargs: "shared_policy",
            policies_to_train=["shared_policy"],
        )
    )
    cfg.train_batch_size_per_learner = 512
    cfg.minibatch_size = 128
    cfg.num_epochs = 3

    print("\nBuilding algorithm...")
    algo = cfg.build_algo()
    print("  Algorithm built successfully.")
    print()

    for i in range(1, 6):
        result = algo.train()
        mean_r = result.get("env_runners", {}).get("episode_return_mean",
                 result.get("episode_return_mean", float("nan")))
        eps    = result.get("env_runners", {}).get("num_episodes",
                 result.get("num_episodes", "?"))
        print(f"  iter {i}/5  reward_mean={mean_r:+.1f}  episodes={eps}")

    print("\n✓ Smoke test complete — training stack works end-to-end.")
    print("  Run a full training on another machine with:")
    print("  python -m ttr_game.agents.train --num-players 4 --num-iters 500")
    ray.shutdown()


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(checkpoint_path: str, num_players: int = 4,
             num_episodes: int = 10,
             expansion: Optional[str] = None,
             expansions: Optional[List[str]] = None) -> None:
    """Load a checkpoint and run evaluation episodes, printing win rates."""
    ray.init(ignore_reinit_error=True)
    cfg = build_config(num_players=num_players, num_env_runners=0,
                       expansion=expansion, expansions=expansions)
    algo = cfg.build_algo()
    algo.restore(checkpoint_path)

    from ..env.ttr_env import TTRMultiAgentEnv
    from ..game.rules import final_scores as compute_final_scores

    env_config: dict = {"num_players": num_players}
    if expansions is not None:
        env_config["expansions"] = expansions
    elif expansion is not None:
        env_config["expansion"] = expansion

    win_counts = [0] * num_players
    for ep in range(num_episodes):
        env = TTRMultiAgentEnv(env_config)
        obs, _ = env.reset()
        done = {"__all__": False}
        while not done["__all__"]:
            agent = env._env.agent_selection
            action = algo.compute_single_action(
                obs.get(agent, obs[list(obs.keys())[0]]),
                policy_id="shared_policy",
            )
            obs, _, done, _, _ = env.step({agent: action})
        scores = compute_final_scores(env._env._state)
        winner = scores.index(max(scores))
        win_counts[winner] += 1
        exp_label = env._env._current_expansion
        print(f"  ep {ep+1:3d}: [{exp_label}] scores={scores}  winner=player_{winner}")

    print(f"\nWin counts ({num_episodes} episodes): {win_counts}")
    ray.shutdown()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from ..env.ttr_env import ALL_EXPANSIONS

    parser = argparse.ArgumentParser(
        description="Train / evaluate TTR Europe RL agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--test", action="store_true",
                        help="Quick smoke test (< 5 min, 2 players, 5 iters)")
    parser.add_argument("--eval", type=str, default=None, metavar="CHECKPOINT",
                        help="Path to checkpoint directory to evaluate")
    parser.add_argument("--num-players",     type=int, default=4)
    parser.add_argument("--num-iters",       type=int, default=500)
    parser.add_argument("--checkpoint-freq", type=int, default=50)
    parser.add_argument("--checkpoint-dir",  type=str, default="./checkpoints")
    parser.add_argument("--num-workers",     type=int, default=4,
                        help="Remote env-runner workers (0 = local only)")
    parser.add_argument("--num-gpus",        type=int, default=0)
    parser.add_argument("--expansion", type=str, default=None,
                        choices=ALL_EXPANSIONS,
                        help="Train/eval on a single expansion variant (default: base)")
    parser.add_argument("--all-expansions", action="store_true",
                        help="Train/eval on all expansion variants (randomly sampled per episode)")
    args = parser.parse_args()

    # Resolve expansion pool
    exp_kwargs: dict = {}
    if args.all_expansions:
        exp_kwargs["expansions"] = ALL_EXPANSIONS
    elif args.expansion:
        exp_kwargs["expansion"] = args.expansion

    if args.test:
        run_test()
    elif args.eval:
        evaluate(args.eval, num_players=args.num_players, **exp_kwargs)
    else:
        train(
            num_players=args.num_players,
            num_iters=args.num_iters,
            checkpoint_freq=args.checkpoint_freq,
            checkpoint_dir=args.checkpoint_dir,
            num_env_runners=args.num_workers,
            num_gpus=args.num_gpus,
            **exp_kwargs,
        )
