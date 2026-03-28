# AI-Basics-UJ

This repository contains two small Python + Pygame projects built around game AI fundamentals. It is meant as a practical collection of experiments with movement, combat, pathfinding, steering, collision handling, and simple decision systems.

If you want to check out the repository, the main value is not polished game content but clear, playable examples of AI-driven behaviors in action.

## What You Will Find Here

- autonomous agents making decisions in real time
- movement and combat systems implemented in a lightweight game setup
- pathfinding and navigation in a constrained arena
- steering behaviors for enemy groups and survival gameplay
- simple, readable project structures for experimenting with AI/gameplay ideas

## Projects

### BotShooter

`BotShooter` is a small autonomous arena simulation where bots fight each other without player control.

What it demonstrates:

- state-based bot behavior
- target seeking, fleeing, and resource gathering
- line-of-sight checks
- A* pathfinding on a generated navigation graph
- ranged combat with rail shots and rockets
- respawn, pickups, and win-condition logic

This part of the repository is the more system-oriented project. It is useful if you want to look at how navigation, combat, and AI state selection can be combined into a complete bot loop.

### MobSurvival

`MobSurvival` is a player-versus-enemies prototype focused on enemy movement and pressure.

What it demonstrates:

- player movement and aiming
- enemy steering and group behavior
- hiding and attacking behavior transitions
- obstacle avoidance and collision handling
- simple survival-style combat with a railgun

This project is useful if you want to inspect more direct gameplay interactions, especially how enemies can feel active and reactive without using heavy AI systems.

## Who This Repository Is For

This repository is a good fit for people who want:

- small AI/gameplay prototypes instead of a large engine-based project
- examples of classic game AI techniques in Python
- code they can modify for coursework, experimentation, or learning
- a starting point for building more advanced bot or survival mechanics

## Tech Stack

- Python
- Pygame

## Notes

- The repository includes two separate prototypes rather than one unified game.
- Some generated `__pycache__` files are present in the project tree.
- The focus is on gameplay logic and AI concepts more than presentation or production packaging.
