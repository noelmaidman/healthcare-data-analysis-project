# AGENTS.md

Guidelines for any AI agent working in this repository.

## Purpose of this project

This is a **learning project**. It follows `Healthcare Data Analyst Project Plan.pdf`: an end-to-end healthcare analytics portfolio (Synthea/FHIR data, Python, BigQuery, dbt, R, scikit-learn, BI dashboard) focused on predicting extended length of stay (LOS > 7 days).

The goal is for the developer to **understand every step**, not just to end up with working code. Speed is secondary. A finished feature the developer cannot explain is a failure.

## Core rule: explain first, implement after approval

**Never write, edit, or run implementation work until the developer has understood and approved the plan.**

Before any implementation, present a plan and stop. Wait for an explicit go-ahead ("ok", "go", "approved", etc.). Silence or a general "continue" about something else is not approval.

### What the plan must contain

1. **Goal**: what we are about to build and which step of the project plan it belongs to (e.g., "Week 3: load Parquet into BigQuery").
2. **Why**: the concept behind it, in plain language (e.g., why Parquet, why explicit schemas, what a window function does).
3. **Approach**: the concrete steps, in order, and the files that will be created or changed.
4. **Key concepts / terms**: short definitions of anything new (FHIR resource, `LAG`, `GroupShuffleSplit`, data leakage, etc.).
5. **Alternatives considered**: other reasonable options, and why this one is recommended.
6. **Risks and pitfalls**: what can go wrong, including data-quality or leakage traps.
7. **Expected result**: what the developer should see when it works, and how we will verify it.
8. **Check for understanding**: end with a question or two so the developer can confirm they follow, and invite them to ask questions or change direction.

Keep it proportionate: a one-line fix needs a two-sentence plan, a new pipeline stage needs the full list.

### During implementation

- Implement **only what was approved**. If scope needs to grow, stop and propose the change first.
- Work in **small steps** the developer can follow, rather than one large drop of code.
- Comment the *why* in code where it teaches something non-obvious. Do not narrate obvious lines.
- After implementing, **walk through the result**: what each part does, what the output means, and how it ties back to the plan.
- If something fails or behaves unexpectedly, explain the cause before proposing a fix. Treat errors as teaching moments.
- Prefer showing the developer how to do something over silently doing it, when it is a skill worth learning (e.g., a SQL query, a dbt test).

## Project-specific guidelines

- **Follow the plan document.** Flag any deviation from it explicitly. For example, the current scripts model *readmission*, while the plan targets *extended LOS*. Ask which is intended instead of assuming.
- **Avoid data leakage.** Model features may only use information known at admission time. Split train/test by patient (`GroupShuffleSplit`), never by row.
- **Reproducibility.** Use fixed seeds (Synthea uses `-s 42`), document commands, and keep the pipeline re-runnable from a clean clone.
- **Never commit large or raw data.** Keep `.gitignore` covering generated data, Parquet outputs, and zip archives. Do not commit anything over 100MB.
- **No secrets in the repo.** Cloud credentials and keys stay out of git.
- **Data is synthetic.** Never present findings as real clinical evidence. Say so in write-ups and the README.
- **Keep the README up to date.** `README.md` must always reflect the current state of the project. Whenever a change affects it, update it in the same piece of work, not later. This includes: new or changed scripts and pipeline stages, setup and run instructions, project structure, tools and dependencies, results and key findings, and completed steps of the plan. Before finishing any task, check whether the README is still accurate. The README is written in English (see Communication). Briefly tell the developer (in Hebrew) what was changed in it.
- **Document as we go.** Update the data dictionary when a stage is completed, in language the developer can later reuse in interviews.

## Git

- Do not commit or push unless the developer asks.
- When asked to commit, use small, descriptive messages that match the existing style (`feat: ...`).

## Communication

- **All explanations, plans, and walkthroughs must be written in Hebrew.** Keep technical terms, identifiers, and file names in English (e.g., "נריץ `LAG` על `patient_id`").
- **Code comments, docstrings, commit messages, and the README are written in English.**
- Be direct about uncertainty. Say "I'm not sure" instead of guessing.
- Give a recommendation, not an exhaustive survey of options.
