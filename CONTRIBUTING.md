# Contributing to AIContentGuard

Thank you for your interest in contributing to AIContentGuard! We welcome contributions from the community to help improve the platform. Whether it's adding new features, fixing bugs, improving documentation, or suggesting ideas, your help is appreciated.

## Getting Started

1.  **Fork the Repository:** Create your own fork of the main AIContentGuard repository on GitHub.
2.  **Clone Your Fork:** Clone your forked repository to your local machine.
    ```bash
    git clone https://github.com/YOUR_USERNAME/ai-content-guard.git
    cd ai-content-guard
    ```
3.  **Set Up Environment:**
    - We recommend using a virtual environment (like `venv` or `conda`).
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate # On Windows use `.venv\Scripts\activate`
      ```
    - Install dependencies:
      ```bash
      pip install -r requirements.txt
      # Install test dependencies if needed (consider a requirements-dev.txt)
      pip install pytest httpx pytest-asyncio
      ```
4.  **Create a Branch:** Create a new branch for your changes. Use a descriptive name (e.g., `feature/add-new-agent`, `fix/api-bug`).
    ```bash
    git checkout -b feature/your-feature-name
    ```

## Development Workflow

1.  **Make Changes:** Implement your feature or bug fix. Follow the project's coding style and structure (see below).
2.  **Write Tests:** Add unit tests (for agents or specific modules) and/or integration tests (for API endpoints) in the `tests/` directory to cover your changes.
3.  **Run Tests:** Ensure all tests pass locally.
    ```bash
    pytest tests/
    ```
4.  **Linting/Formatting (Optional but Recommended):** Use tools like `black` and `flake8` or `ruff` to ensure code quality and consistency.
5.  **Commit Changes:** Commit your changes with clear and concise commit messages.
    ```bash
    git add .
    git commit -m "feat: Add new sentiment analysis agent"
    # Or: git commit -m "fix: Correct handling of empty input in controller"
    ```
6.  **Push Changes:** Push your branch to your fork on GitHub.
    ```bash
    git push origin feature/your-feature-name
    ```
7.  **Create a Pull Request (PR):** Open a pull request from your branch in your fork to the `main` branch of the original AIContentGuard repository.
    - Provide a clear title and description for your PR, explaining the changes and referencing any related issues.
    - Ensure the PR template (if available) is filled out.

## Project Structure & Conventions

- **Directory Structure:** Familiarize yourself with the project structure outlined in the `README.md` or technical guide.
  - `app/`: Core application code (FastAPI, agents, config, etc.).
  - `app/agents/`: Individual agent implementations.
  - `tests/`: Unit and integration tests.
  - `data/`: Sample data.
  - `deploy/`: Deployment guides.
- **Coding Style:**
  - Follow PEP 8 guidelines.
  - Use type hints for function signatures and variables.
  - Write clear docstrings for public classes and functions.
  - Keep functions and classes focused on a single responsibility.
- **Agent Structure:** When adding a new agent:
  - Create a new file in `app/agents/`.
  - Inherit from `app.agents.base.BaseAgent`.
  - Implement `__init__`, `predict`, `normalize_output`, `health_check`, and `get_metadata` methods.
  - Ensure the agent loads its model ID from `app.config.settings`.
  - Add configuration (model ID, thresholds) to `.env.example`.
  - Register the agent in the controller or agent registry (e.g., `agent_registry.yaml` if used).
  - Add unit tests for the new agent in `tests/test_agents.py`.
- **Configuration:** Use environment variables (`.env` file loaded via `app.config.py`) for configuration. Provide defaults and document new variables in `.env.example`.
- **Logging:** Use the centralized logger from `app.logger.get_logger()`. Include relevant context in log messages.
- **Dependencies:** Add new Python dependencies to `requirements.txt`.

## Testing Checklist

Before submitting a PR, ensure:

- [ ] Your code changes achieve the intended goal.
- [ ] New unit or integration tests covering the changes have been added.
- [ ] All existing and new tests pass (`pytest tests/`).
- [ ] The code adheres to PEP 8 and project conventions.
- [ ] Documentation (docstrings, README, guides) has been updated if necessary.
- [ ] `.env.example` is updated if new configuration variables were added.
- [ ] The `CHANGELOG.md` includes a note about your contribution (especially for features or breaking changes).

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. (If a CODE_OF_CONDUCT.md file exists, link to it here).

## Reporting Issues

If you find a bug or have a feature request, please check the existing issues first. If your issue isn't listed, create a new one, providing as much detail as possible.

Thank you for contributing!
