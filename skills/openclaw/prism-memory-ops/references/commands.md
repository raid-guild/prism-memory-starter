# Prism Memory Ops Commands

Run from repo root with:

```bash
PYTHONPATH=superprism_poc/raidguild/code
```

## Targeted Commands

```bash
python3 -m community_memory.pipeline collect --base superprism_poc --space raidguild
python3 -m community_memory.pipeline digest --base superprism_poc --space raidguild --date YYYY-MM-DD
python3 -m community_memory.pipeline memory --base superprism_poc --space raidguild --date YYYY-MM-DD
python3 -m community_memory.pipeline seeds --base superprism_poc --space raidguild --date YYYY-MM-DD
python3 -m community_memory.pipeline backup --base superprism_poc --space raidguild
```

## Force Regeneration

```bash
python3 -m community_memory.pipeline digest --base superprism_poc --space raidguild --date YYYY-MM-DD --force
python3 -m community_memory.pipeline memory --base superprism_poc --space raidguild --date YYYY-MM-DD --force
python3 -m community_memory.pipeline seeds --base superprism_poc --space raidguild --date YYYY-MM-DD --force
```

## Full Scheduled Loop

```bash
python3 -m community_memory.pipeline run --base superprism_poc --space raidguild
```

Use this only when testing schedule behavior or running normal daily automation.
