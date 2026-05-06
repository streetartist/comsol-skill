# Thermal + Electromagnetic Workflows

This reference is for heat transfer, electromagnetics, and especially their coupling.

## Official COMSOL Signals

Primary sources:

- Busbar walkthrough in LiveLink for MATLAB intro: <https://doc.comsol.com/6.4/doc/com.comsol.help.llmatlab/IntroductionToLiveLinkForMATLAB.pdf>
- Heat Transfer in Solids reference: <https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_ref_heattransfer.30.10.html>
- Electromagnetic heating theory: <https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_theory.07.092.html>
- Frequency-Transient, One-Way Electromagnetic Heating study: <https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_ref_solver.36.092.html>

Key official points:

- COMSOL provides a Heat Transfer in Solids interface for conduction-driven solid thermal models.
- COMSOL provides electromagnetic heating interfaces built around the Electromagnetic Heating multiphysics coupling.
- The electromagnetic heating theory page explicitly lists Joule Heating, Induction Heating, Laser Heating, and Microwave Heating as supported interface families.
- The LiveLink busbar example shows the core electrothermal pattern:
  - create electric-current physics with `ConductiveMedia`
  - create heat-transfer physics
  - create `ElectromagneticHeating` multiphysics coupling

## Local Application Library Shortlist

Relevant local examples detected on this machine:

- `applications\ACDC_Module\Electromagnetic_Heating\heating_circuit.mph`
- `applications\ACDC_Module\Electromagnetic_Heating\igbt_joule_heating.mph`
- `applications\ACDC_Module\Electromagnetic_Heating\inductive_heating.mph`
- `applications\ACDC_Module\Electromagnetic_Heating\induction_heating_cu*.mph`
- `applications\Heat_Transfer_Module\Applications\inline_induction_heate*.mph`
- multiple `Power_Electronics_and_Electronic_Cooling` models under the Heat Transfer Module

When the user asks for a busbar, current lead, IGBT, conductor heating, coil heating, induction heater, or electronics cooling problem, inspect the closest local library model first.

For a waveguide launching microwaves into a water target, the closest local starting points are usually:

- `RF_Module\Microwave_Heating\microwave_cancer_therapy.mph`
- `RF_Module\Microwave_Heating\microwave_oven.mph`
- `RF_Module\Transmission_Lines_and_Waveguides\waveguide_*.mph`
- `RF_Module\Microwave_Heating\conical_dielectric_probe.mph`

The practical route is to copy the nearest example, convert it to editable code when possible, then replace the applicator/object geometry and material model with the project-specific waveguide and water cylinder.

Important local caveat:

- Some installed Application Library `.mph` files on this machine are only preview placeholders. If `mphopen(...)` reports that the model is an Application Library preview file, open COMSOL Desktop, download the full example from the Application Library UI, and then retry the scripted workflow on the downloaded `.mph`.

## Template Selection

- `heat-transfer-square-2d`
  - Use to validate thermal materials, sources, and boundary conditions in isolation.
- `electrostatics-square-2d`
  - Use to validate geometry, selections, and electrical loading in a simpler field-only setup.
- `electrothermal-joule-heating-square-2d`
  - Use as the default starter for Joule heating and electrothermal coupling.

## Practical Modeling Rule

For coupled thermal-electromagnetic work, do not jump straight into the fully coupled model unless the setup is already stable.

Preferred order:

1. Validate geometry and selections.
2. Validate the thermal-only or electrical-only baseline.
3. Add the coupling.
4. Verify source transfer, units, and boundary conditions before trusting the final temperatures.

## What The Current Skill Covers Well

- heat-transfer-only starter model generation
- electric or electrostatic starter model generation
- Joule-heating-style electrothermal starter model generation
- end-to-end batch execution and export

## What Still Needs Custom Work Per Project

- realistic geometry import
- temperature-dependent material laws
- radiation, convection, or fluid coupling
- induction or RF-specific setups
- frequency-to-transient chained studies
