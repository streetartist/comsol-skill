---
name: comsol-multiphysics
description: "Use when Codex needs to operate a local COMSOL Multiphysics installation end to end: locating COMSOL on the machine, opening or editing `.mph` models, building or modifying models in the Desktop, running studies or parametric sweeps in batch mode, exporting plots/data/reports, starting COMSOL Multiphysics Server and connecting clients, automating through model methods or the COMSOL API for Java, using LiveLink for MATLAB when available, or compiling COMSOL applications."
---

# COMSOL Multiphysics

Use the local COMSOL installation instead of improvising command lines. Start by discovering the installation, then choose the execution mode that matches the task.

## Quick Start

1. Run `python scripts/comsol_tool.py discover`.
2. Read [local-installation.md](./references/local-installation.md) if you are working on this machine.
3. Read [official-workflows.md](./references/official-workflows.md) when you need command/API/export details or official doc links.
4. For from-scratch project creation, prefer the validated pipeline in `scripts/comsol_project_builder.py` before hand-writing Java from scratch.
5. Prefer copying the source model to a new output path before destructive changes. When working through the Java API, prefer `ModelUtil.loadCopy(...)` over in-place edits.
6. Keep a `batchlog` or equivalent log file for every nontrivial solve.

## Workflow Decision Tree

- Use Desktop when the task requires creating geometry, physics, mesh, studies, plots, or exports interactively from scratch.
- Use `batch` when the task starts from an existing `.mph` or Java class file and the goal is solving, sweeping, or running a method reproducibly.
- Use `mphserver` plus `mphclient` when the task requires client/server separation, repeated client connections, or MATLAB integration through the server.
- Use model methods, the Java Shell, or the COMSOL API for Java when the user wants scripted model construction or deterministic edits.
- For zero-to-end automation on this machine, prefer the validated `spec -> Java -> compile -> batch -> outputs` path before trying GUI automation.
- Use `compile` when the deliverable is a redistributable compiled COMSOL application rather than an `.mph` model.
- Use LiveLink for MATLAB only when the user explicitly wants MATLAB or you confirm the local installation and license support that route.

## Thermal + Electromagnetic Focus

For this machine and this skill, split thermal-electromagnetic work into three levels:

- Heat-only baseline:
  - Use `heat-transfer-square-2d` when validating thermal material data, source terms, or thermal boundary conditions before adding electromagnetics.
- Electric or electrostatic baseline:
  - Use `electrostatics-square-2d` or adapt its structure to electric-current-only studies when validating electrical loading and selections.
- Coupled electrothermal workflow:
  - Use `electrothermal-joule-heating-square-2d` for conduction-current-driven heating.
  - Use this as the base pattern for busbars, resistive heaters, PCB traces, current-carrying conductors, and similar Joule heating problems.

For induction, microwave, or frequency-transient heating, read [thermal-electromagnetic.md](./references/thermal-electromagnetic.md) and start from the closest local Application Library model before authoring a new template.

## Validated From-Scratch Path

Use this first when the user asks to create a model from zero and drive the entire lifecycle automatically.

1. Copy or initialize a JSON spec.
2. Render the Java model source from the spec.
3. Compile the Java source with `comsolcompile`.
4. Run the compiled class with `comsolbatch`.
5. Inspect the generated `.mph`, exported image, exported numerical table, and `run.log`.

Validated commands:

```powershell
python scripts/comsol_project_builder.py init-spec --template electrothermal-joule-heating-square-2d --output scratch\starter-spec.json
python scripts/comsol_project_builder.py run --spec scratch\starter-spec.json
```

Validated templates currently include:

- `electrostatics-square-2d`
- `heat-transfer-square-2d`
- `electrothermal-joule-heating-square-2d`

For your main workflow, start with `electrothermal-joule-heating-square-2d`. It creates a new COMSOL model from zero, builds geometry, mesh, electric-current and heat-transfer physics, adds the electromagnetic heating coupling, solves, exports temperature and current-density images, exports a temperature table, and saves an `.mph` model.

When the user asks for a different physics problem, use the validated template as a base and adapt the generated Java source or author a new Java model using the same workflow.

## Standard Operating Procedure

### 1. Inspect the machine first

- Run `python scripts/comsol_tool.py discover`.
- If COMSOL is not on `PATH`, use the absolute executable paths reported by the script.
- Confirm the version before using version-specific guidance.
- Discovery is version-flexible: prefer `COMSOLROOT` or `--root` when supplied, otherwise scan registry entries and common `COMSOL*` installation folders.
- Treat installed example libraries and local folders as evidence of availability, not proof that every module license is checked out at runtime.

### 2. Define the modeling contract

- Lock down the exact input files, requested physics/modules, parameters to vary, expected outputs, and whether the user wants an updated `.mph`, exported artifacts, a method, or a compiled app.
- If the user describes a physics problem but not a COMSOL artifact, decide whether to start from an application-library example or from a new Desktop model.
- If the task is risky or expensive, state the intended solve path before launching long runs.

### 3. Choose the execution mode

- Desktop:
  - Launch with `python scripts/comsol_tool.py desktop --detach`.
  - Use when creating or editing model structure interactively.
- Validated template pipeline:
  - Use `python scripts/comsol_project_builder.py run --spec <spec.json>` when starting from zero with a supported template.
  - Use this path when the request is deterministic enough to encode in a JSON spec and Java template.
  - Default to the electrothermal template for coupled heat-electromagnetic work unless the requested physics clearly calls for induction, microwave, or another specialized interface.
- Batch:
  - Use for reproducible solves of an existing `.mph`.
  - Example: `python scripts/comsol_tool.py batch --inputfile model.mph --outputfile solved.mph --study std1 --batchlog solved.log`.
- Batch with methods or sweeps:
  - Use `--methodcall`, `--methodinputfile`, `--paramfile`, `--pname`, `--plist`, or `--pindex`.
  - Put complex input values in a file instead of cramming them into one shell line.
- Server/client:
  - Start server with `python scripts/comsol_tool.py server --port 2036 --detach`.
  - Connect a client with `python scripts/comsol_tool.py client --host localhost --port 2036 --detach`.
- Java/API:
  - Use Desktop methods, the Java Shell, or exported Java model files when deterministic scripted changes are required.
  - Compile Java source or COMSOL applications with `python scripts/comsol_tool.py compile <file>`.
- MATLAB:
  - Use `scripts/comsol_matlab_bridge.py` when the requested workflow is MATLAB-centric or when the agent needs flexible scripted edits on an existing `.mph`.
  - This skill uses the validated `matlab.exe -batch -> mphstartcomsolmphserver -> mphstart -> mphopen/mphsave` route on this machine.
  - For `.m` or `.java` export, allow the bridge to sanitize the temporary codegen filename; COMSOL rejects some stems such as names containing `-`.

### 4. Preserve inputs and logs

- Do not overwrite the only copy of an input model unless the user explicitly asks for it.
- Prefer separate `input`, `output`, and `logs` paths.
- For batch jobs, always set `--batchlog`.
- For long jobs, place outputs in a dedicated run directory and keep the exact command line.

### 5. Postprocess intentionally

- Decide up front whether the user needs:
  - an updated `.mph`;
  - exported images, animations, tables, or text data;
  - a generated report;
  - a compiled application;
  - method or Java source artifacts for future reruns.
- When exporting from batch jobs, verify whether file paths should resolve on the batch side or the Desktop side.

### 6. Validate and close out

- Read the batch log or command stderr before claiming success.
- Report the study tag, parameter set, output paths, and any warnings that matter for reproducibility.
- If you started a server or detached GUI process, tell the user exactly what was launched and on which port/path.

## Command Patterns

```powershell
# Discover the local installation
python scripts/comsol_tool.py discover

# Show version and CLI help
python scripts/comsol_tool.py version
python scripts/comsol_tool.py help comsolbatch

# Launch Desktop or Client/Server
python scripts/comsol_tool.py desktop --detach
python scripts/comsol_tool.py server --port 2036 --detach
python scripts/comsol_tool.py client --host localhost --port 2036 --detach

# Solve an existing model
python scripts/comsol_tool.py batch --inputfile model.mph --outputfile solved.mph --study std1 --batchlog solved.log

# Create, solve, postprocess, and export from a validated zero-start template
python scripts/comsol_project_builder.py init-spec --template electrothermal-joule-heating-square-2d --output scratch\starter-spec.json
python scripts/comsol_project_builder.py run --spec scratch\starter-spec.json

# Run a method call
python scripts/comsol_tool.py batch --inputfile app.mph --outputfile app-out.mph --methodcall runCase --methodinputfile inputs.txt --batchlog app.log

# Compile Java or a COMSOL application
python scripts/comsol_tool.py compile model.java
python scripts/comsol_tool.py compile app.mph --outputdir build

# Search/copy a local example, then convert or script it through MATLAB LiveLink
python scripts/comsol_examples.py search microwave waveguide heating water --limit 12
python scripts/comsol_examples.py copy --source "D:\path\to\example.mph" --dest scratch\case.mph
python scripts/comsol_matlab_bridge.py convert --cwd scratch --input scratch\case.mph --output scratch\case.java
python scripts/comsol_matlab_bridge.py run-script --cwd scratch --model scratch\case.mph --script scratch\edit_case.m --save scratch\case-edited.mph

# Use a less common launcher directly
python scripts/comsol_tool.py exec comsolpowerpointbatch -- -help
```

## Resources

- `scripts/comsol_tool.py`
  - Discover the local installation, print version/help, and launch the common COMSOL entry points from one stable interface.
- `scripts/comsol_project_builder.py`
  - Render and run validated from-scratch COMSOL project templates.
- `scripts/comsol_examples.py`
  - Search local Application Library models and copy the closest reference model into a working directory.
- `scripts/comsol_matlab_bridge.py`
  - Run MATLAB LiveLink scripts against a COMSOL model and convert `.mph` files to `.m` or `.java` through `matlab.exe -batch` and COMSOL's `mli` server helpers.
- [references/local-installation.md](./references/local-installation.md)
  - Machine-specific facts discovered on this workstation.
- [references/official-workflows.md](./references/official-workflows.md)
  - Official COMSOL command/API/export guidance with links.
- [references/thermal-electromagnetic.md](./references/thermal-electromagnetic.md)
  - Thermal, electromagnetic, and coupled-workflow guidance oriented to Joule heating, induction heating, and related models.
- [references/validated-workflows.md](./references/validated-workflows.md)
  - Real end-to-end workflows validated on this machine, including COMSOL batch/class caveats.

## Escalation Rules

- If COMSOL is missing, the detected version conflicts with the task, or the requested module/license is unavailable, stop and report the exact blocker.
- If the user asks for a fully modeled physics solution but provides insufficient geometry/material/boundary-condition details, push for the missing engineering inputs instead of fabricating them.
- If a requested solve may take a long time, produce a reproducible run plan and log location before launching it.
