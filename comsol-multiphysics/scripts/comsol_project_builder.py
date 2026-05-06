#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from comsol_tool import resolve_executable  # noqa: E402


DEFAULT_SPECS = {
    "electrostatics-square-2d": {
        "template": "electrostatics-square-2d",
        "class_name": "ElectrostaticsSquareProject",
        "model_label": "Electrostatics Square Project",
        "output_dir": "./outputs/electrostatics-square-project",
        "geometry": {
            "size": "1",
            "length_unit": "m",
        },
        "physics": {
            "ground_boundary": 1,
            "potential_boundary": 3,
            "potential_value": "1[V]",
        },
        "study": {
            "type": "Stationary",
        },
        "postprocess": {
            "primary_plot_expression": "V",
            "table_expression": "V",
            "table_label": "Max electric potential",
        },
        "exports": {
            "mph_filename": "electrostatics-square.mph",
            "primary_image_filename": "potential.png",
            "table_filename": "max-potential.txt",
            "batchlog_filename": "run.log",
        },
    },
    "heat-transfer-square-2d": {
        "template": "heat-transfer-square-2d",
        "class_name": "HeatTransferSquareProject",
        "model_label": "Heat Transfer Square Project",
        "output_dir": "./outputs/heat-transfer-square-project",
        "geometry": {
            "size": "1",
            "length_unit": "m",
        },
        "material": {
            "thermalconductivity": "15[W/(m*K)]",
            "density": "7800[kg/m^3]",
            "heatcapacity": "500[J/(kg*K)]",
        },
        "physics": {
            "boundary_temperature": "293.15[K]",
            "heat_source": "1e6[W/m^3]",
        },
        "study": {
            "type": "Stationary",
        },
        "postprocess": {
            "primary_plot_expression": "T",
            "table_expression": "T",
            "table_label": "Max temperature",
        },
        "exports": {
            "mph_filename": "heat-transfer-square.mph",
            "primary_image_filename": "temperature.png",
            "table_filename": "max-temperature.txt",
            "batchlog_filename": "run.log",
        },
    },
    "electrothermal-joule-heating-square-2d": {
        "template": "electrothermal-joule-heating-square-2d",
        "class_name": "ElectroThermalJouleHeatingProject",
        "model_label": "Electrothermal Joule Heating Square Project",
        "output_dir": "./outputs/electrothermal-joule-heating-square-project",
        "geometry": {
            "size": "1",
            "length_unit": "m",
        },
        "material": {
            "electricconductivity": "5.998e7[S/m]",
            "thermalconductivity": "400[W/(m*K)]",
            "density": "8960[kg/m^3]",
            "heatcapacity": "385[J/(kg*K)]",
        },
        "physics": {
            "ground_boundary": 1,
            "potential_boundary": 3,
            "potential_value": "1[V]",
            "boundary_temperature": "293.15[K]",
        },
        "study": {
            "type": "Stationary",
        },
        "postprocess": {
            "primary_plot_expression": "T",
            "secondary_plot_expression": "ec.normJ",
            "table_expression": "T",
            "table_label": "Max temperature",
        },
        "exports": {
            "mph_filename": "electrothermal-joule-heating-square.mph",
            "primary_image_filename": "temperature.png",
            "secondary_image_filename": "current-density.png",
            "table_filename": "max-temperature.txt",
            "batchlog_filename": "run.log",
        },
    },
}


def load_spec(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    template = data.get("template")
    if template not in DEFAULT_SPECS:
        raise SystemExit(f"Unsupported template: {template}")
    return data


def java_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def relative_filename(value: str) -> str:
    return f".\\\\{value}"


def common_header(class_name: str) -> str:
    return f"""import com.comsol.model.*;
import com.comsol.model.util.*;

public class {class_name} {{
  public static void main(String[] args) throws Exception {{
    run();
  }}

"""


def common_footer() -> str:
    return """}
"""


def render_electrostatics(spec: dict, spec_path: Path) -> tuple[str, Path]:
    class_name = spec["class_name"]
    model_label = spec.get("model_label", class_name)
    output_dir = resolve_output_dir(spec, spec_path)
    exports = spec["exports"]
    geometry = spec["geometry"]
    physics = spec["physics"]
    postprocess = spec["postprocess"]

    source = common_header(class_name) + f"""  public static Model run() throws Exception {{
    String mphFile = "{java_escape(relative_filename(exports["mph_filename"]))}";
    String pngFile = "{java_escape(relative_filename(exports["primary_image_filename"]))}";
    String tableFile = "{java_escape(relative_filename(exports["table_filename"]))}";

    Model model = ModelUtil.create("Model");
    model.label("{java_escape(model_label)}");

    model.component().create("comp1");
    model.component("comp1").geom().create("geom1", 2);
    model.component("comp1").geom("geom1").lengthUnit("{java_escape(geometry["length_unit"])}");
    model.component("comp1").geom("geom1").create("sq1", "Square");
    model.component("comp1").geom("geom1").feature("sq1").set("size", "{java_escape(str(geometry["size"]))}");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").mesh().create("mesh1", "geom1");
    model.component("comp1").mesh("mesh1").create("ftri1", "FreeTri");
    model.component("comp1").mesh("mesh1").run();

    model.component("comp1").physics().create("es", "Electrostatics", "geom1");
    model.component("comp1").physics("es").feature().create("gnd1", "Ground", 1);
    model.component("comp1").physics("es").feature("gnd1").selection().set(new int[]{{{int(physics["ground_boundary"])}}});
    model.component("comp1").physics("es").feature().create("pot1", "ElectricPotential", 1);
    model.component("comp1").physics("es").feature("pot1").selection().set(new int[]{{{int(physics["potential_boundary"])}}});
    model.component("comp1").physics("es").feature("pot1").set("V0", 1, "{java_escape(physics["potential_value"])}");

    model.study().create("std1");
    model.study("std1").feature().create("stat1", "{java_escape(spec["study"]["type"])}");
    model.study("std1").run();

    model.result().create("pg1", "PlotGroup2D");
    model.result("pg1").label("Electric Potential");
    model.result("pg1").set("data", "dset1");
    model.result("pg1").create("surf1", "Surface");
    model.result("pg1").feature("surf1").set("expr", "{java_escape(postprocess["primary_plot_expression"])}");
    model.result("pg1").run();

    model.result().numerical().create("max1", "MaxSurface");
    model.result().numerical("max1").selection().set(new int[]{{1}});
    model.result().numerical("max1").set("expr", new String[]{{"{java_escape(postprocess["table_expression"])}"}});
    model.result().table().create("tbl1", "Table");
    model.result().table("tbl1").comments("{java_escape(postprocess["table_label"])}");
    model.result().numerical("max1").set("table", "tbl1");
    model.result().numerical("max1").setResult();

    model.result().export().create("img1", "pg1", "Image");
    model.result().export("img1").set("imagetype", "png");
    model.result().export("img1").set("pngfilename", pngFile);
    model.result().export("img1").run();

    model.result().export().create("tblExp", "Table");
    model.result().export("tblExp").set("table", "tbl1");
    model.result().export("tblExp").set("filename", tableFile);
    model.result().export("tblExp").run();

    model.save(mphFile);
    return model;
  }}
""" + common_footer()
    return source, output_dir


def render_heat_transfer(spec: dict, spec_path: Path) -> tuple[str, Path]:
    class_name = spec["class_name"]
    model_label = spec.get("model_label", class_name)
    output_dir = resolve_output_dir(spec, spec_path)
    exports = spec["exports"]
    geometry = spec["geometry"]
    material = spec["material"]
    physics = spec["physics"]
    postprocess = spec["postprocess"]

    source = common_header(class_name) + f"""  public static Model run() throws Exception {{
    String mphFile = "{java_escape(relative_filename(exports["mph_filename"]))}";
    String pngFile = "{java_escape(relative_filename(exports["primary_image_filename"]))}";
    String tableFile = "{java_escape(relative_filename(exports["table_filename"]))}";

    Model model = ModelUtil.create("Model");
    model.label("{java_escape(model_label)}");

    model.component().create("comp1");
    model.component("comp1").geom().create("geom1", 2);
    model.component("comp1").geom("geom1").lengthUnit("{java_escape(geometry["length_unit"])}");
    model.component("comp1").geom("geom1").create("sq1", "Square");
    model.component("comp1").geom("geom1").feature("sq1").set("size", "{java_escape(str(geometry["size"]))}");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").mesh().create("mesh1", "geom1");
    model.component("comp1").mesh("mesh1").create("ftri1", "FreeTri");
    model.component("comp1").mesh("mesh1").run();

    model.component("comp1").material().create("mat1", "Common");
    model.component("comp1").material("mat1").propertyGroup("def").set("thermalconductivity", new String[]{{"{java_escape(material["thermalconductivity"])}"}});
    model.component("comp1").material("mat1").propertyGroup("def").set("density", "{java_escape(material["density"])}");
    model.component("comp1").material("mat1").propertyGroup("def").set("heatcapacity", "{java_escape(material["heatcapacity"])}");

    model.component("comp1").physics().create("ht", "HeatTransfer", "geom1");
    model.component("comp1").physics("ht").feature().create("temp1", "TemperatureBoundary", 1);
    model.component("comp1").physics("ht").feature("temp1").selection().all();
    model.component("comp1").physics("ht").feature("temp1").set("T0", 1, "{java_escape(physics["boundary_temperature"])}");
    model.component("comp1").physics("ht").feature().create("hs1", "HeatSource", 2);
    model.component("comp1").physics("ht").feature("hs1").selection().all();
    model.component("comp1").physics("ht").feature("hs1").set("Q0", "{java_escape(physics["heat_source"])}");

    model.study().create("std1");
    model.study("std1").feature().create("stat1", "{java_escape(spec["study"]["type"])}");
    model.study("std1").run();

    model.result().create("pg1", "PlotGroup2D");
    model.result("pg1").label("Temperature");
    model.result("pg1").set("data", "dset1");
    model.result("pg1").create("surf1", "Surface");
    model.result("pg1").feature("surf1").set("expr", "{java_escape(postprocess["primary_plot_expression"])}");
    model.result("pg1").run();

    model.result().numerical().create("max1", "MaxSurface");
    model.result().numerical("max1").selection().set(new int[]{{1}});
    model.result().numerical("max1").set("expr", new String[]{{"{java_escape(postprocess["table_expression"])}"}});
    model.result().table().create("tbl1", "Table");
    model.result().table("tbl1").comments("{java_escape(postprocess["table_label"])}");
    model.result().numerical("max1").set("table", "tbl1");
    model.result().numerical("max1").setResult();

    model.result().export().create("img1", "pg1", "Image");
    model.result().export("img1").set("imagetype", "png");
    model.result().export("img1").set("pngfilename", pngFile);
    model.result().export("img1").run();

    model.result().export().create("tblExp", "Table");
    model.result().export("tblExp").set("table", "tbl1");
    model.result().export("tblExp").set("filename", tableFile);
    model.result().export("tblExp").run();

    model.save(mphFile);
    return model;
  }}
""" + common_footer()
    return source, output_dir


def render_electrothermal(spec: dict, spec_path: Path) -> tuple[str, Path]:
    class_name = spec["class_name"]
    model_label = spec.get("model_label", class_name)
    output_dir = resolve_output_dir(spec, spec_path)
    exports = spec["exports"]
    geometry = spec["geometry"]
    material = spec["material"]
    physics = spec["physics"]
    postprocess = spec["postprocess"]

    source = common_header(class_name) + f"""  public static Model run() throws Exception {{
    String mphFile = "{java_escape(relative_filename(exports["mph_filename"]))}";
    String tempFile = "{java_escape(relative_filename(exports["primary_image_filename"]))}";
    String currentFile = "{java_escape(relative_filename(exports["secondary_image_filename"]))}";
    String tableFile = "{java_escape(relative_filename(exports["table_filename"]))}";

    Model model = ModelUtil.create("Model");
    model.label("{java_escape(model_label)}");

    model.component().create("comp1");
    model.component("comp1").geom().create("geom1", 2);
    model.component("comp1").geom("geom1").lengthUnit("{java_escape(geometry["length_unit"])}");
    model.component("comp1").geom("geom1").create("sq1", "Square");
    model.component("comp1").geom("geom1").feature("sq1").set("size", "{java_escape(str(geometry["size"]))}");
    model.component("comp1").geom("geom1").run();

    model.component("comp1").mesh().create("mesh1", "geom1");
    model.component("comp1").mesh("mesh1").create("ftri1", "FreeTri");
    model.component("comp1").mesh("mesh1").run();

    model.component("comp1").material().create("mat1", "Common");
    model.component("comp1").material("mat1").propertyGroup("def").set("electricconductivity", new String[]{{"{java_escape(material["electricconductivity"])}"}});
    model.component("comp1").material("mat1").propertyGroup("def").set("thermalconductivity", new String[]{{"{java_escape(material["thermalconductivity"])}"}});
    model.component("comp1").material("mat1").propertyGroup("def").set("density", "{java_escape(material["density"])}");
    model.component("comp1").material("mat1").propertyGroup("def").set("heatcapacity", "{java_escape(material["heatcapacity"])}");

    model.component("comp1").physics().create("ec", "ConductiveMedia", "geom1");
    model.component("comp1").physics("ec").feature().create("gnd1", "Ground", 1);
    model.component("comp1").physics("ec").feature("gnd1").selection().set(new int[]{{{int(physics["ground_boundary"])}}});
    model.component("comp1").physics("ec").feature().create("pot1", "ElectricPotential", 1);
    model.component("comp1").physics("ec").feature("pot1").selection().set(new int[]{{{int(physics["potential_boundary"])}}});
    model.component("comp1").physics("ec").feature("pot1").set("V0", 1, "{java_escape(physics["potential_value"])}");

    model.component("comp1").physics().create("ht", "HeatTransfer", "geom1");
    model.component("comp1").physics("ht").feature().create("temp1", "TemperatureBoundary", 1);
    model.component("comp1").physics("ht").feature("temp1").selection().all();
    model.component("comp1").physics("ht").feature("temp1").set("T0", 1, "{java_escape(physics["boundary_temperature"])}");

    model.component("comp1").multiphysics().create("emh", "ElectromagneticHeating");
    model.component("comp1").multiphysics("emh").selection().all();

    model.study().create("std1");
    model.study("std1").feature().create("stat1", "{java_escape(spec["study"]["type"])}");
    model.study("std1").run();

    model.result().create("pg1", "PlotGroup2D");
    model.result("pg1").label("Temperature");
    model.result("pg1").set("data", "dset1");
    model.result("pg1").create("surf1", "Surface");
    model.result("pg1").feature("surf1").set("expr", "{java_escape(postprocess["primary_plot_expression"])}");
    model.result("pg1").run();

    model.result().create("pg2", "PlotGroup2D");
    model.result("pg2").label("Current Density");
    model.result("pg2").set("data", "dset1");
    model.result("pg2").create("surf1", "Surface");
    model.result("pg2").feature("surf1").set("expr", "{java_escape(postprocess["secondary_plot_expression"])}");
    model.result("pg2").run();

    model.result().numerical().create("max1", "MaxSurface");
    model.result().numerical("max1").selection().set(new int[]{{1}});
    model.result().numerical("max1").set("expr", new String[]{{"{java_escape(postprocess["table_expression"])}"}});
    model.result().table().create("tbl1", "Table");
    model.result().table("tbl1").comments("{java_escape(postprocess["table_label"])}");
    model.result().numerical("max1").set("table", "tbl1");
    model.result().numerical("max1").setResult();

    model.result().export().create("img1", "pg1", "Image");
    model.result().export("img1").set("imagetype", "png");
    model.result().export("img1").set("pngfilename", tempFile);
    model.result().export("img1").run();

    model.result().export().create("img2", "pg2", "Image");
    model.result().export("img2").set("imagetype", "png");
    model.result().export("img2").set("pngfilename", currentFile);
    model.result().export("img2").run();

    model.result().export().create("tblExp", "Table");
    model.result().export("tblExp").set("table", "tbl1");
    model.result().export("tblExp").set("filename", tableFile);
    model.result().export("tblExp").run();

    model.save(mphFile);
    return model;
  }}
""" + common_footer()
    return source, output_dir


def resolve_output_dir(spec: dict, spec_path: Path) -> Path:
    output_dir = Path(spec.get("output_dir", "."))
    if not output_dir.is_absolute():
        output_dir = (spec_path.parent / output_dir).resolve()
    return output_dir


def render_spec(spec: dict, spec_path: Path) -> tuple[str, Path]:
    template = spec["template"]
    if template == "electrostatics-square-2d":
        return render_electrostatics(spec, spec_path)
    if template == "heat-transfer-square-2d":
        return render_heat_transfer(spec, spec_path)
    if template == "electrothermal-joule-heating-square-2d":
        return render_electrothermal(spec, spec_path)
    raise SystemExit(f"Unsupported template: {template}")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_command(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec).resolve()
    spec = load_spec(spec_path)
    java_source, output_dir = render_spec(spec, spec_path)
    java_out = Path(args.java_out).resolve() if args.java_out else output_dir / f"{spec['class_name']}.java"
    write_text(java_out, java_source)
    print(json.dumps({"java_file": str(java_out), "output_dir": str(output_dir), "template": spec["template"]}, indent=2))
    return 0


def run_subprocess(command: list[str], cwd: Path | None = None) -> None:
    completed = subprocess.run(command, cwd=str(cwd) if cwd else None, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def write_batch_prefs(output_dir: Path) -> Path:
    prefs_dir = output_dir / "comsol-batch-prefs"
    prefs_file = prefs_dir / "comsol.prefs"
    write_text(
        prefs_file,
        "\n".join(
            [
                "security.comsol.allowapplications=on",
                "security.comsol.allowbatch=on",
                "security.comsol.allowmethods=on",
                "security.external.enable=off",
                "",
            ]
        ),
    )
    return prefs_dir


def run_command(args: argparse.Namespace) -> int:
    spec_path = Path(args.spec).resolve()
    spec = load_spec(spec_path)
    java_source, output_dir = render_spec(spec, spec_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    java_file = output_dir / f"{spec['class_name']}.java"
    write_text(java_file, java_source)

    compile_exe = resolve_executable(args.root, "comsolcompile")
    batch_exe = resolve_executable(args.root, "comsolbatch")

    run_subprocess([compile_exe, str(java_file)])

    class_file = java_file.with_suffix(".class")
    batchlog = output_dir / spec["exports"]["batchlog_filename"]
    prefs_dir = write_batch_prefs(output_dir)
    run_subprocess(
        [
            batch_exe,
            "-prefsdir",
            str(prefs_dir),
            "-inputfile",
            str(class_file),
            "-batchlog",
            str(batchlog),
        ],
        cwd=output_dir,
    )

    outputs = {
        "mph": str(output_dir / spec["exports"]["mph_filename"]),
        "primary_image": str(output_dir / spec["exports"]["primary_image_filename"]),
        "table": str(output_dir / spec["exports"]["table_filename"]),
    }
    if "secondary_image_filename" in spec["exports"]:
        outputs["secondary_image"] = str(output_dir / spec["exports"]["secondary_image_filename"])

    summary = {
        "template": spec["template"],
        "java_file": str(java_file),
        "class_file": str(class_file),
        "batchlog": str(batchlog),
        "prefs_dir": str(prefs_dir),
        "outputs": outputs,
    }
    print(json.dumps(summary, indent=2))
    return 0


def init_spec_command(args: argparse.Namespace) -> int:
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    template = args.template
    output.write_text(json.dumps(DEFAULT_SPECS[template], indent=2), encoding="utf-8")
    print(str(output))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and run validated COMSOL project templates.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    init_spec = subparsers.add_parser("init-spec", help="Write a starter JSON spec.")
    init_spec.add_argument("--template", choices=sorted(DEFAULT_SPECS.keys()), default="electrothermal-joule-heating-square-2d", help="Template to initialize.")
    init_spec.add_argument("--output", required=True, help="Path to write the starter JSON spec.")
    init_spec.set_defaults(func=init_spec_command)

    render = subparsers.add_parser("render", help="Render Java source from a JSON spec.")
    render.add_argument("--spec", required=True, help="Path to a JSON spec.")
    render.add_argument("--java-out", help="Optional explicit Java output path.")
    render.set_defaults(func=render_command)

    run = subparsers.add_parser("run", help="Render, compile, and execute a JSON spec.")
    run.add_argument("--spec", required=True, help="Path to a JSON spec.")
    run.add_argument("--root", help="Optional COMSOL installation root override.")
    run.set_defaults(func=run_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
