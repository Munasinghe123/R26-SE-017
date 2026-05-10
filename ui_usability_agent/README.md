# UI/UX Usability Agent

This repository contains the UI/UX & Usability Agent used in the SLIIT undergraduate dissertation project on a multi-agent LLM-based framework for early-phase software engineering.

The agent takes structured software requirements, plans the screens that need to be built, generates UI prototypes with an LLM, and evaluates each prototype against three standards:

- ISO 9241-11 proxy metrics using BeautifulSoup4
- Nielsen heuristic proxy metrics using BeautifulSoup4
- WCAG 2.2 accessibility checks using axe-core / Node.js

The current workflow is implemented as separate planning, generation, and evaluation phases controlled from `main.py`.

## Web Interface

The project includes a Next.js-based web interface for interactive use without the command line.

### Features

- **Planning**: Input requirements JSON to plan screens
- **Generation**: Generate UI prototypes for selected screens
- **Evaluation**: Evaluate prototypes against ISO 9241-11, Nielsen heuristics, and WCAG 2.2 standards
- **Persistence**: Sessions persist across browser refreshes and server restarts
- **Clear Session**: "New Session" button to clear all data and start fresh

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000

### API Routes

- `POST /api/plan` - Plan screens from requirements
- `POST /api/generate` - Generate UI for a screen
- `POST /api/evaluate` - Evaluate screens
- `GET /api/outputs` - List generated screens
- `GET /api/reports` - List evaluation reports
- `POST /api/clear-session` - Clear all session data (screen plan, generated screens, reports)

## How it works

1. Load requirements from `samples/sample_requirements.json`.
2. Normalize the input with `input_normalizer.py`.
3. Ask the LLM-based screen planner to identify the screens that should be built.
4. Generate a UI for one selected screen using the prompt template in `prompts/generation_prompt.txt`.
5. Evaluate the generated HTML with the composite scorer.
6. Save the screen plan and score reports to `outputs/`.

The current generator uses Groq via `langchain-groq`, not a local Ollama runtime.

## Project structure

```text
ui_usability_agent/
├── evaluator/
│   ├── iso_metrics.py
│   ├── nielsen_metrics.py
│   ├── wcag_metrics.py
│   └── composite_scorer.py
├── generator/
│   ├── ui_generator.py
│   └── refinement_controller.py
├── prompts/
│   ├── generation_prompt.txt
│   └── refinement_templates.py
├── samples/
│   ├── bad_ui.html
│   └── good_ui.html
├── outputs/
│   ├── generated_screens/
│   ├── score_reports/
│   └── screen_plan.json
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── clear-session/
│   │   │   │   │   └── route.js
│   │   │   │   ├── evaluate/
│   │   │   │   │   └── route.js
│   │   │   │   ├── generate/
│   │   │   │   │   └── route.js
│   │   │   │   ├── outputs/
│   │   │   │   │   └── route.js
│   │   │   │   ├── plan/
│   │   │   │   │   └── route.js
│   │   │   │   ├── plan-status/
│   │   │   │   │   └── route.js
│   │   │   │   └── reports/
│   │   │   │       └── route.js
│   │   │   ├── preview/
│   │   │   │   └── [screenId]/
│   │   │   │       └── page.js
│   │   │   ├── reports/
│   │   │   │   └── [screenId]/
│   │   │   │       └── page.js
│   │   │   ├── globals.css
│   │   │   ├── layout.js
│   │   │   └── page.js
│   │   └── components/
│   │       ├── DocumentationTabs.js
│   │       ├── Header.js
│   │       ├── InputForm.js
│   │       └── UIOutput.js
│   ├── package.json
│   ├── next.config.mjs
│   └── ...
├── input_normalizer.py
├── main.py
├── screen_planner.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10+
- Node.js LTS (for frontend and axe-core accessibility checks)
- A Groq API key in `ui_usability_agent/.env` as `GROQ_API_KEY`
- `axe` CLI installed globally: `npm install -g @axe-core/cli`

## Installation

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

If you do not already have a `ui_usability_agent/.env` file, create one with your Groq key:

```env
GROQ_API_KEY=your_key_here
```

Install Node.js LTS from https://nodejs.org, then install the Axe CLI and frontend dependencies:

```bash
npm install -g @axe-core/cli
cd frontend
npm install
```

## Usage

Run the screen planning phase:

```bash
python main.py --plan
```

Generate one screen from the saved plan:

```bash
python main.py --generate login
```

You can also use the screen number shown in the plan output:

```bash
python main.py --generate 1
```

Evaluate all generated screens:

```bash
python main.py --evaluate
```

If you run `python main.py` with no flags, the script prints the available commands.

## Outputs

- `outputs/screen_plan.json` stores the planned screens.
- `outputs/generated_screens/` stores generated HTML files per screen.
- `outputs/score_reports/` stores one JSON score report per generated screen.

## Scoring summary

The composite score combines three weighted dimensions:

- ISO 9241-11 proxy metrics: 30%
- Nielsen heuristic proxy metrics: 30%
- WCAG 2.2 accessibility: 40%

`evaluator/composite_scorer.py` prints a Rich score table when `rich` is installed and falls back to plain text otherwise.

## Notes

- `generator/ui_generator.py` currently requires `GROQ_API_KEY` and uses the Groq-hosted Llama models configured in code.
- `evaluator/wcag_metrics.py` uses a Node-based axe-core runner when available and falls back to the CLI when needed.
- `refinement_controller.py` is present as a placeholder for the targeted refinement loop.

## References

- ISO 9241-11:2018
- Nielsen, J. (1994). 10 Usability Heuristics
- W3C WCAG 2.2

