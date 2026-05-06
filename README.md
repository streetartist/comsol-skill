# Skill for Cosmol

Skill for operating a local COMSOL Multiphysics installation end to end.

It supports installation discovery, COMSOL command launching, Java model compilation, batch solving, local Application Library search, JSON-driven starter model generation, and MATLAB LiveLink automation when available.

Chinese documentation: [README.zh-CN.md](README.zh-CN.md)

## Repository Layout

```text
comsol-skill/
  README.md
  README.zh-CN.md
  .gitignore
  comsol-multiphysics/
    SKILL.md
    agents/
      openai.yaml
    assets/
      specs/
        electrostatics-square-2d.json
        heat-transfer-square-2d.json
        electrothermal-joule-heating-square-2d.json
    references/
      local-installation.md
      official-workflows.md
      thermal-electromagnetic.md
      validated-workflows.md
    scripts/
      comsol_tool.py
      comsol_project_builder.py
      comsol_examples.py
      comsol_matlab_bridge.py
```

## Capabilities

- Discover local COMSOL installations across multiple versions.
- Launch COMSOL Desktop, batch solver, server, client, compiler, and other command-line tools.
- Compile Java model files with `comsolcompile`.
- Run `.mph` models or compiled Java `.class` models with `comsolbatch`.
- Generate complete starter models from JSON specs.
- Export `.mph`, PNG images, and numerical TXT tables from supported templates.
- Search and copy local Application Library examples.
- Run MATLAB LiveLink workflows through local MATLAB batch execution when available.
- Preserve run logs and avoid overwriting input models by default.

## Version-Flexible Discovery

The skill is not tied to one COMSOL release. Discovery checks:

1. explicit `--root`
2. `COMSOLROOT`
3. COMSOL registry entries
4. common versioned install folders such as `COMSOL62`, `COMSOL63`, `COMSOL64`, and future `COMSOL*` directories

You can pass either the COMSOL installation root or the platform binary directory:

```powershell
python scripts\comsol_tool.py discover --root "D:\path\to\COMSOLxx\Multiphysics"
python scripts\comsol_tool.py discover --root "D:\path\to\COMSOLxx\Multiphysics\bin\win64"
```

## Quick Start

Run commands from the skill directory:

```powershell
cd path\to\comsol-skill\comsol-multiphysics
```

Discover COMSOL:

```powershell
python scripts\comsol_tool.py discover
```

Create a starter spec:

```powershell
python scripts\comsol_project_builder.py init-spec `
  --template heat-transfer-square-2d `
  --output .\scratch\spec.json
```

Run the generated model:

```powershell
python scripts\comsol_project_builder.py run `
  --spec .\scratch\spec.json
```

Expected output structure:

```text
scratch/
  outputs/
    heat-transfer-square-project/
      heat-transfer-square.mph
      temperature.png
      max-temperature.txt
      run.log
```

## Validated Starter Templates

- `electrostatics-square-2d`
- `heat-transfer-square-2d`
- `electrothermal-joule-heating-square-2d`

These templates are intended as reliable starting points for scripted COMSOL automation. For a different physics problem, adapt the closest template or start from a relevant local Application Library example.

## Common Commands

Show version:

```powershell
python scripts\comsol_tool.py version
```

Launch Desktop:

```powershell
python scripts\comsol_tool.py desktop --detach
```

Open a model in Desktop:

```powershell
python scripts\comsol_tool.py desktop path\to\model.mph --detach
```

Run an existing model in batch:

```powershell
python scripts\comsol_tool.py batch `
  --inputfile path\to\input.mph `
  --outputfile path\to\solved.mph `
  --study std1 `
  --batchlog path\to\solved.log
```

Compile Java:

```powershell
python scripts\comsol_tool.py compile path\to\MyModel.java
```

Search local Application Library examples:

```powershell
python scripts\comsol_examples.py search microwave heating --limit 10
```

Copy an Application Library model:

```powershell
python scripts\comsol_examples.py copy `
  --source path\to\example.mph `
  --dest path\to\working-copy.mph
```

## Batch Export Security

Some COMSOL versions restrict file-system access for Java methods and batch-class workflows. This can prevent image or table exports even when the solve itself succeeds.

`scripts/comsol_project_builder.py run` handles this for generated template runs by creating an isolated preferences directory under the output directory:

```text
<output_dir>\comsol-batch-prefs\comsol.prefs
```

This avoids changing the user's global COMSOL preferences.

## MATLAB LiveLink

The skill includes `scripts/comsol_matlab_bridge.py` for MATLAB-centric workflows.

Use this route only after confirming that MATLAB and COMSOL LiveLink are installed and licensed. Typical tasks include:

- converting `.mph` models to `.m` or `.java`
- running MATLAB scripts against an existing COMSOL model
- saving edited `.mph` models through MATLAB batch execution

## Operating Guidelines

- Run `discover` first on a new machine.
- Use explicit output directories for nontrivial solves.
- Keep a batch log for reproducibility.
- Do not overwrite the only copy of an input `.mph` unless explicitly requested.
- Treat Application Library folders as evidence of installed examples, not proof that every required module license is available.
- Define geometry, materials, boundary conditions, study settings, and expected exports before launching expensive solves.

## Troubleshooting

### COMSOL Not Found

Pass an explicit root:

```powershell
python scripts\comsol_tool.py discover --root "D:\path\to\COMSOLxx\Multiphysics"
```

Or set `COMSOLROOT`:

```powershell
$env:COMSOLROOT = "D:\path\to\COMSOLxx\Multiphysics"
python scripts\comsol_tool.py discover
```

### Version Probe Times Out

If `version` is `null` and `version_warning` reports a timeout, the installation may still be usable. Check whether command paths exist and run a small template simulation.

### Export Files Are Missing

Check the batch log for file-system security errors. If using `comsol_project_builder.py run`, confirm that the output directory contains:

```text
comsol-batch-prefs\comsol.prefs
```

### Application Library Model Fails to Open

Some local Application Library `.mph` entries may be placeholders. Open or download the full example through COMSOL Desktop's Application Library UI, then retry automation.

