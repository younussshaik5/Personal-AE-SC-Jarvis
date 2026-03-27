# Contributing to JARVIS

First off, thank you for considering contributing to JARVIS! This project aims to provide an autonomous, self-evolving AI assistant tailored for Presales and Solutions Consulting professionals.

## How to Contribute

### 1. Adding New Skills
The skill system is modular. To add a new skill:
1. Create a new Python file in `jarvis/skills/`
2. Define a class that implements your skill logic (subscribing to events)
3. Register your skill in `jarvis/core/orchestrator.py`
4. Submit a Pull Request!

### 2. Improving Personas
Personas define how JARVIS behaves. You can:
- Improve existing personas in `persona/`
- Add new personas (e.g., Customer Success Manager, Account Executive)
- Submit your persona template as a PR.

### 3. Core Engine Improvements
If you're interested in the core engine (Event Bus, Observers, Learners):
- Please open an issue to discuss your proposed architectural changes first.
- Ensure all components handle asynchronous events gracefully.

## Development Setup
Check the `README.md` and `docs/getting-started/START_HERE.md` for full installation instructions. 

**Quick test commands:**
- `./fireup_jarvis.sh` to start the entire stack
- `python -m pytest tests/` to run all tests

## Code of Conduct
Please be respectful and constructive in all issues and pull requests.
