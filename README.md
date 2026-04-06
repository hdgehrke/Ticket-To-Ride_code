# Ticket to Ride: Europe

A complete implementation of Ticket to Ride: Europe with:
- **Hot-seat multiplayer** — any mix of human and CPU players on one computer
- **RL training** — Ray RLlib PPO agent with action masking and self-play

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Playing Hot-Seat

All players share one computer and take turns. Between turns the screen clears so the active player can see their private hand and tickets without others peeking.

**All humans (4 players):**
```bash
python -m ttr_game.play
```

**Choose the number of players:**
```bash
python -m ttr_game.play --players 3
```

**Mix humans and CPU players:**

Pass `--ai` with the 0-based player indices you want the CPU to control.

```bash
# 3 humans + 1 CPU (player 4 is CPU)
python -m ttr_game.play --players 4 --ai 3

# 2 humans + 2 CPUs (players 3 and 4 are CPU)
python -m ttr_game.play --players 4 --ai 2 3

# Watch 4 CPUs play each other
python -m ttr_game.play --players 4 --ai 0 1 2 3
```

**Reproduce a game with a fixed seed:**
```bash
python -m ttr_game.play --players 4 --ai 3 --seed 42
```

### Hot-seat flow

1. You'll be asked to enter a name for each human player.
2. When it's your turn, the screen clears and prompts: *"Pass to [name], press Enter."* Other players look away while you enter your name to confirm.
3. Your hand and tickets are shown privately.
4. Choose from a numbered action menu — draw cards, claim a route, draw destination tickets, or place a station.
5. CPU turns are played automatically with a short pause so you can follow along.
6. At game end, final scores and rankings are displayed.

**Use a trained RL model for CPU players:**
```bash
python -m ttr_game.play --players 4 --ai 3 --model ./checkpoints/<checkpoint_dir>
```

> **Note:** Without `--model`, CPU players choose randomly. Once you've trained an agent (see below), pass the checkpoint path to use it.

---

## Training the RL Agent

### Quick smoke test (< 5 minutes)

Run this before a full training to confirm the entire stack works on your machine:

```bash
python -m ttr_game.agents.train --test
```

Expected output (numbers will vary):
```
==============================================================
  TTR Europe — RL stack smoke test
  2 players · 5 iterations · local mode (no remote workers)
==============================================================

Building algorithm...
  Algorithm built successfully.

  iter 1/5  reward_mean=+24.0  episodes=2
  iter 2/5  reward_mean=+55.0  episodes=3
  iter 3/5  reward_mean=+53.7  episodes=3
  iter 4/5  reward_mean=+78.8  episodes=4
  iter 5/5  reward_mean=+62.3  episodes=3

✓ Smoke test complete — training stack works end-to-end.
```

### Full training run

Run this on a machine with more CPU (or GPU) cores. Each iteration runs several complete games in parallel.

```bash
# 4-player self-play, 500 iterations, save checkpoint every 50
python -m ttr_game.agents.train --num-players 4 --num-iters 500

# With GPU and more parallel workers
python -m ttr_game.agents.train --num-players 4 --num-iters 500 --num-workers 8 --num-gpus 1

# 2-player (faster training, simpler game)
python -m ttr_game.agents.train --num-players 2 --num-iters 500
```

Checkpoints are saved to `./checkpoints/` every 50 iterations by default.

**Key flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--num-players` | 4 | Players per game (2–5) |
| `--num-iters` | 500 | Training iterations |
| `--checkpoint-freq` | 50 | Save checkpoint every N iters |
| `--checkpoint-dir` | `./checkpoints` | Where to save checkpoints |
| `--num-workers` | 4 | Parallel env-runner processes (0 = local only) |
| `--num-gpus` | 0 | GPUs for the learner |

### Evaluating a checkpoint

```bash
python -m ttr_game.agents.train --eval ./checkpoints/<checkpoint_dir> --num-players 4
```

---

## Running Tests

```bash
pytest ttr_game/tests/ -v
```

---

## Web Multiplayer Server (in development)

A FastAPI + WebSocket server for playing over a network is implemented but the frontend is not yet built.

```bash
uvicorn ttr_game.server.app:app --reload
# API docs at http://localhost:8000/docs
```
