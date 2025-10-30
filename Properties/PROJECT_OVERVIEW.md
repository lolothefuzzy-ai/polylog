# Project Overview

## Intent

This project is an advanced engine for the automated placement and folding of polygons to create complex 2D and 3D structures. The core purpose is to simulate and study the principles of self-assembly, where complex forms emerge from the interaction of simpler units.

The engine intelligently evaluates possible connections between polygons, attempts to fold them into stable configurations, and manages failures through a process of "decay" and "reformation." This allows for the continuous and autonomous exploration of a vast design space of possible polyform assemblies.

## Current Trajectory

The project is currently focused on enhancing the intelligence, performance, and analytical capabilities of the engine. The key development trajectories are:

1. **Performance and Scalability:** Implementing advanced caching strategies (multi-level in-memory and disk caching) and spatial partitioning data structures (Bounding Volume Hierarchy) to handle increasingly large and complex assemblies.

2. **Sophisticated Optimization:** Integrating powerful optimization libraries like SciPy and Optuna to move beyond simple heuristics. This allows for:
    * **Constraint-based optimization** of fold angles to achieve desired geometric properties (e.g., stability, spacing).
    * **Bayesian optimization** of exploration strategies to discover the most efficient paths to complex assemblies.

3. **Canonical Analysis:** Developing a system for "Canonical N" tracking, which provides a standardized measure of assembly complexity and diversity. This enables:
    * **Quantitative tracking** of the evolutionary process.
    * **Comparison** of different growth strategies and parameter sets.
    * **Deeper insights** into the principles of the simulated self-assembly.

4. **API-Driven Architecture:** Building a robust API server to expose the engine's functionality, allowing it to be controlled and integrated with external tools, such as a graphical user interface for visualization and interaction.

5. **Desktop Application:** The project is intended to be packaged as a standalone desktop application for Windows, facilitating its use and distribution.

In essence, the project is evolving from a basic geometric folding engine into a sophisticated scientific tool for exploring and understanding the principles of emergent complexity in self-assembling systems.
