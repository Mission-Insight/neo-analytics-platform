# neo-analytics-platform

This produces a risk model for near-Earth objects.

## Project Structure

```text
src/
data/
tests/
docs/
notebooks/
scripts/
```

### Directory Overview

| Directory | Purpose |
|---|---|
| `src/` | Core application source code |
| `data/` | Raw and processed datasets |
| `tests/` | Unit and integration tests |
| `docs/` | Project documentation |
| `notebooks/` | Jupyter notebooks and experiments |
| `scripts/` | Utility and automation scripts |

---

## Environment Setup

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### macOS/Linux

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

Current dependencies include:

- pandas
- numpy
- requests
- streamlit
- pytest
- python-dotenv

---

## Environment Variables

Create a local `.env` file using the provided template:

```bash
cp .env.example .env
```

Example:

```env
NASA_API_KEY=your_api_key_here
```

---

## Development Tooling

This project is configured with:

- Black formatting
- Flake8 linting
- VS Code debug profiles
- Format-on-save
- Real-time lint diagnostics

---

## Running Validation

### Format Code

```bash
black .
```

### Run Linting

```bash
flake8 .
```

### Run Tests

```bash
pytest
```

---

## Debugging

VS Code launch configurations are included for:

- Fetch scripts
- Streamlit dashboard
- Unit testing

Use the **Run and Debug** panel in VS Code to launch configurations.

---

## Git Workflow

Development should occur on feature branches:

```bash
git checkout -b feature/my-feature
```

Branch protection rules are enabled for `main`.

---

## Status

Initial project scaffolding and development environment setup completed.