# Local Installation Snapshot

This reference captures facts discovered on this workstation, last checked on 2026-05-07.

## Detected Installation

- COMSOL root: `D:\Program Files\COMSOL\COMSOL62\Multiphysics`
- Version from `comsolbatch -version`: currently unavailable because the version probe timed out after 20 seconds.
- The previous `D:\Students\CYS\Software\COMSOL64\Multiphysics` installation path was not present during the 2026-05-07 check.
- `Get-Command comsol*` returned nothing, so COMSOL is not currently on the shell `PATH`.
- `scripts/comsol_tool.py discover` is not tied to this exact version. It checks `COMSOLROOT`, COMSOL registry entries, and versioned install directories such as `COMSOL62`, `COMSOL63`, `COMSOL64`, and future `COMSOL*` folders under common Windows roots.

## Executables Present

The following Windows launchers were detected under `bin\win64`:

- `comsol.exe`
- `comsolbatch.exe`
- `comsolcompile.exe`
- `comsolmethodexec.exe`
- `comsolmphclient.exe`
- `comsolmphserver.exe`
- `comsolpowerpointbatch.exe`
- `comsoldoc.exe`
- `comsolxpl.exe`

Use `python scripts/comsol_tool.py discover` for exact absolute paths before launching anything.

## Local Documentation

The installation includes local PDF manuals under:

- `doc\pdf\COMSOL_Multiphysics\ApplicationProgrammingGuide.pdf`
- `doc\pdf\COMSOL_Multiphysics\COMSOL_ApplicationBuilderManual.pdf`
- `doc\pdf\COMSOL_Multiphysics\COMSOL_PostprocessingAndVisualization.pdf`
- `doc\pdf\COMSOL_Multiphysics\COMSOL_ProgrammingReferenceManual.pdf`
- `doc\pdf\COMSOL_Multiphysics\COMSOL_ReferenceManual.pdf`
- `doc\pdf\COMSOL_Multiphysics\IntroductionToCOMSOLMultiphysics.pdf`

These manuals are useful when the online documentation is insufficient or when exact 6.2 behavior matters.

## Application Libraries and Examples

The installation contains populated `applications\` folders for many modules, including:

- `COMSOL_Multiphysics`
- `Structural_Mechanics_Module`
- `Heat_Transfer_Module`
- `CFD_Module`
- `ACDC_Module`
- multiple `LiveLink_*` folders

Treat these folders as local example content and starting points. Do not assume every example is licensed for execution until the needed module checks out successfully.

## MATLAB / LiveLink Signals

- The `mli\` tree is present.
- MATLAB-facing `.m` files such as `mphapplicationlibraries.m`, `mphbatchinfo.m`, `mpheval.m`, and `mphgeom.m` were detected.
- Local MATLAB was also detected at `D:\Students\CYS\Matlab R2024b\bin\matlab.exe`.

This strongly suggests that LiveLink for MATLAB files are installed locally. Still validate runtime licensing before promising MATLAB automation.

## COMSOL With MATLAB Initialization Note

The official COMSOL-with-MATLAB client-server mode stores a username and password in user preferences on first launch.

On this workstation, non-interactive `comsolmphserver matlab ...` execution currently reports missing login information. That means:

- the bridge tooling is present;
- MATLAB itself is installed;
- but COMSOL-with-MATLAB likely still needs one interactive first run to establish the saved credentials.

## License Notes

- `licenseinfo.ini` exists locally and indicates a locally configured license.
- Do not copy license serials, vendor strings, or license files into generated artifacts unless the user explicitly asks for licensing diagnostics.
- When batch licenses matter, use `-usebatchlic` and report that choice explicitly.
