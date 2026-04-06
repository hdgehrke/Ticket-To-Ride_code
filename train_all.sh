#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# train_all.sh  —  Sequential training for all player counts, all expansions
#
# Target hardware: AMD Ryzen 5 5600X (6c/12t), 32 GB RAM, RTX 3060 12 GB
#
# Usage:
#   chmod +x train_all.sh
#   ./train_all.sh              # default 1000 iters per run
#   ./train_all.sh --iters 500  # shorter run for testing
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults (tune here if needed)
# ---------------------------------------------------------------------------
ITERS=1000          # training iterations per player-count model
CKPT_FREQ=100       # save a checkpoint every N iters
CKPT_DIR="./checkpoints"
WORKERS=4           # Ray env-runner processes (leave 2 threads for driver + learner)
GPUS=1              # RTX 3060: use 1 GPU for the learner
LOG_DIR="./logs"

# ---------------------------------------------------------------------------
# Parse optional flags
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --iters)    ITERS="$2";     shift 2 ;;
        --workers)  WORKERS="$2";   shift 2 ;;
        --gpus)     GPUS="$2";      shift 2 ;;
        --ckpt-dir) CKPT_DIR="$2";  shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
mkdir -p "$LOG_DIR"
START_TIME=$(date +%s)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "========================================================"
echo "  Ticket to Ride — Full Training Run"
echo "  Started: $(date)"
echo "  Iters per model : $ITERS"
echo "  Checkpoint every: $CKPT_FREQ iters"
echo "  Env runners      : $WORKERS"
echo "  GPUs             : $GPUS"
echo "  Checkpoints in  : $CKPT_DIR"
echo "  Logs in         : $LOG_DIR"
echo "========================================================"

PLAYER_COUNTS=(2 3 4 5)
FAILED=()

# ---------------------------------------------------------------------------
# Helper: run one training job and stream output to both terminal and log file
# ---------------------------------------------------------------------------
run_job() {
    local players=$1
    local log_file="$LOG_DIR/players_${players}_${TIMESTAMP}.log"
    local ckpt_subdir="$CKPT_DIR/players_${players}"

    echo ""
    echo "--------------------------------------------------------"
    echo "  Starting: $players-player model  (log → $log_file)"
    echo "  $(date)"
    echo "--------------------------------------------------------"

    python -m ttr_game.agents.train \
        --num-players    "$players"    \
        --num-iters      "$ITERS"      \
        --checkpoint-freq "$CKPT_FREQ" \
        --checkpoint-dir  "$ckpt_subdir" \
        --num-workers    "$WORKERS"    \
        --num-gpus       "$GPUS"       \
        --all-expansions \
        2>&1 | tee "$log_file"
}

# ---------------------------------------------------------------------------
# Main loop — run each player count in sequence
# ---------------------------------------------------------------------------
for players in "${PLAYER_COUNTS[@]}"; do
    if run_job "$players"; then
        echo "  ✓ $players-player training complete"
    else
        echo "  ✗ $players-player training FAILED (exit $?)"
        FAILED+=("$players")
        echo "  Continuing to next player count..."
    fi
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
END_TIME=$(date +%s)
ELAPSED=$(( END_TIME - START_TIME ))
HOURS=$(( ELAPSED / 3600 ))
MINS=$(( (ELAPSED % 3600) / 60 ))

echo ""
echo "========================================================"
echo "  Training complete: $(date)"
echo "  Total elapsed: ${HOURS}h ${MINS}m"
echo ""

if [[ ${#FAILED[@]} -eq 0 ]]; then
    echo "  All 4 models trained successfully."
    echo ""
    echo "  Checkpoints:"
    for players in "${PLAYER_COUNTS[@]}"; do
        latest=$(ls -td "$CKPT_DIR/players_${players}"/checkpoint_* 2>/dev/null | head -1 || echo "  (none)")
        echo "    $players-player: $latest"
    done
else
    echo "  WARNING: ${#FAILED[@]} job(s) failed: ${FAILED[*]}"
    echo "  Check the logs in $LOG_DIR for details."
fi

echo "========================================================"
