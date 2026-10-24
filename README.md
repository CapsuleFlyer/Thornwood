# Thornwood Rescue

AI course project: four missions (hill climbing / simulated annealing, genetic
algorithm, minimax, alpha-beta pruning) reported as an "Owl Cipher".

## Submission files

| File | Purpose |
|------|---------|
| `thornwood.py` | All four missions. No input; prints only the 36-line Owl Cipher report. |
| `debrief.pdf` | Debrief report, max 4 pages, answers the five Chapter 5 questions. |

## Run

Requires Python 3.10+ and the standard library only.

```bash
python thornwood.py
```

## Repo layout

```
thornwood.py        submission: all missions
debrief.pdf         submission: debrief (max 4 pages)
README.md
.gitignore
extras/             NOT part of the submission
  debrief_runs.py   extra experiments the debrief asks for
  debrief.md        source text for debrief.pdf
```

## Missions

1. **The false summit**: hill climbing, random restart, simulated annealing
2. **Rin's seedcraft**: genetic algorithm, verified by brute force
3. **Eyes that see the future**: full and depth-limited minimax (Stone Drop)
4. **Running on empty**: alpha-beta pruning (Stone Drop + Master Hyo's tree)

## Notes

- Randomness uses `random.Random(seed)` with `rng.random()` only.
- No hard-coded answers: every value is computed at run time.
