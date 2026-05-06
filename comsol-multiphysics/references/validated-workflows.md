# Validated Workflows

This file records workflows that were actually executed on this workstation, not just inferred from the manuals.

## 2026-03-21: Pure COMSOL From-Scratch Pipelines

Validated path:

1. Generate Java from a JSON spec with `scripts/comsol_project_builder.py`
2. Compile with `comsolcompile`
3. Run the compiled class with `comsolbatch`
4. Inspect the generated `.mph`, `png`, `txt`, and `run.log`

Validated specs:

- [electrostatics-square-2d.json](../assets/specs/electrostatics-square-2d.json)
- [heat-transfer-square-2d.json](../assets/specs/heat-transfer-square-2d.json)
- [electrothermal-joule-heating-square-2d.json](../assets/specs/electrothermal-joule-heating-square-2d.json)

Validated outputs produced during testing:

- `scratch\outputs\electrostatics-square-project\electrostatics-square.mph`
- `scratch\outputs\electrostatics-square-project\potential.png`
- `scratch\outputs\electrostatics-square-project\max-potential.txt`
- `scratch\outputs\electrostatics-square-project\run.log`
- `scratch\outputs\heat-transfer-square-project\heat-transfer-square.mph`
- `scratch\outputs\heat-transfer-square-project\temperature.png`
- `scratch\outputs\heat-transfer-square-project\max-temperature.txt`
- `scratch\outputs\electrothermal-joule-heating-square-project\electrothermal-joule-heating-square.mph`
- `scratch\outputs\electrothermal-joule-heating-square-project\temperature.png`
- `scratch\outputs\electrothermal-joule-heating-square-project\current-density.png`
- `scratch\outputs\electrothermal-joule-heating-square-project\max-temperature.txt`

Observed result from the exported table:

- Max electric potential reported as `1.06`
- Heat-only max temperature reported as `5204.341112209931`
- Coupled electrothermal max temperature reported as `19362.386775786432`

## Important COMSOL Batch/Class Caveats

- When a compiled Java class is run through `comsolbatch`, the `args` value can be `null`. Do not assume `args.length` is safe.
- In this batch/class route, direct absolute-path file access from Java can trigger COMSOL file-system security errors.
- Relative paths of the form `.\file.ext` worked reliably in the validated run.
- On COMSOL 6.2, Java result exports can still fail with a file-system access security error unless batch is started with an isolated preferences directory containing `security.external.enable=off`. `scripts/comsol_project_builder.py run` now writes and uses `comsol-batch-prefs\comsol.prefs` automatically for generated template runs.
- COMSOL also emitted an additional auto-saved file named like `<ClassName>_Model.mph` in the run directory. Treat this as runtime side effect, not the primary deliverable.

## What This Validates

This validated path proves that on this machine the skill can:

- create a COMSOL project from zero;
- build geometry, mesh, physics, and study by code;
- build heat-transfer-only models;
- build coupled electrothermal models using electric currents plus electromagnetic heating;
- solve the model in batch mode;
- create postprocessing nodes;
- export one or more images;
- export numerical results to text;
- save an `.mph` model.

## What Is Not Yet Validated Here

- Automatic GUI clicking inside COMSOL Desktop
- Report export from the Java batch path
- Arbitrary physics templates beyond the validated electrostatics, heat-transfer, and Joule-heating electrothermal templates
- Induction-heating and RF-specific starter templates

## 2026-03-21: Flexible Toolchain Validation

Validated flexible tools:

- `scripts/comsol_examples.py search`
- `scripts/comsol_examples.py copy`
- `scripts/comsol_matlab_bridge.py convert`
- `scripts/comsol_matlab_bridge.py run-script`

Validated result:

- Searching `microwave waveguide heating water` returned local RF and microwave-heating examples including `microwave_cancer_therapy.mph`, `microwave_oven.mph`, and waveguide-related RF models.
- Copying `microwave_cancer_therapy.mph` into a working directory succeeded.
- Converting `scratch\outputs\heat-transfer-square-project\heat-transfer-square.mph` to `scratch\outputs\heat-transfer-square-project\heat-transfer-square.m` succeeded through MATLAB batch mode.
- Running a custom MATLAB script against `scratch\outputs\heat-transfer-square-project\heat-transfer-square.mph` and saving `scratch\outputs\heat-transfer-square-project\heat-transfer-square-scripted.mph` succeeded.
- The script smoke test also created `scratch\run_script_marker.txt`, proving that arbitrary MATLAB-side logic ran inside the bridge workflow.

Observed caveats:

- The `comsolmphserver matlab` wrapper path was not stable enough on this workstation for agent automation.
- The validated bridge path is `matlab.exe -batch` plus COMSOL `mli` helpers: `mphstartcomsolmphserver`, `mphstart`, `mphopen`, and `mphsave`.
- When exporting to `.m` or `.java`, COMSOL rejects some file stems, for example names containing `-`. The bridge now sanitizes the temporary codegen filename and renames the exported file back to the requested path.
- Some locally installed Application Library `.mph` files are preview placeholders, not full downloadable models. Attempting to `mphopen(...)` those placeholders fails until the real example is downloaded through COMSOL's Application Library UI.
