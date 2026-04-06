PYTHON      ?= python
PLAYERS     ?= 4
ITERS       ?= 500
CKPT_FREQ   ?= 50
CKPT_DIR    ?= ./checkpoints
WORKERS     ?= 4
GPUS        ?= 0
EXPANSION   ?= base

# ── Quick checks ────────────────────────────────────────────────────────────

test:
	pytest ttr_game/tests/ -v

smoke:
	$(PYTHON) -m ttr_game.agents.train --test

# ── Training ─────────────────────────────────────────────────────────────────

## Train on a single expansion (EXPANSION=base|1912|europe_expanded|big_cities|mega)
train:
	$(PYTHON) -m ttr_game.agents.train \
		--num-players  $(PLAYERS) \
		--num-iters    $(ITERS) \
		--checkpoint-freq $(CKPT_FREQ) \
		--checkpoint-dir  $(CKPT_DIR) \
		--num-workers  $(WORKERS) \
		--num-gpus     $(GPUS) \
		--expansion    $(EXPANSION)

## Train on ALL five expansion variants simultaneously (recommended for a general agent)
train-all:
	$(PYTHON) -m ttr_game.agents.train \
		--num-players  $(PLAYERS) \
		--num-iters    $(ITERS) \
		--checkpoint-freq $(CKPT_FREQ) \
		--checkpoint-dir  $(CKPT_DIR) \
		--num-workers  $(WORKERS) \
		--num-gpus     $(GPUS) \
		--all-expansions

# ── Evaluation ───────────────────────────────────────────────────────────────

## Evaluate a checkpoint on all expansions (CKPT=<path>)
eval-all:
	$(PYTHON) -m ttr_game.agents.train \
		--eval         $(CKPT) \
		--num-players  $(PLAYERS) \
		--all-expansions

## Evaluate a checkpoint on a single expansion (CKPT=<path> EXPANSION=<variant>)
eval:
	$(PYTHON) -m ttr_game.agents.train \
		--eval         $(CKPT) \
		--num-players  $(PLAYERS) \
		--expansion    $(EXPANSION)

# ── Web server ───────────────────────────────────────────────────────────────

server:
	uvicorn ttr_game.server.app:app --reload

.PHONY: test smoke train train-all eval eval-all server
