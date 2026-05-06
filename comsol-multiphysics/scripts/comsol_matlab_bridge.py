#!/usr/bin/env python
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from comsol_tool import detect_installation  # noqa: E402


def matlab_root(explicit_mlroot: str | None, explicit_matlab: str | None) -> Path:
    if explicit_mlroot:
        path = Path(explicit_mlroot).resolve()
        if path.exists():
            return path
        raise SystemExit(f"MATLAB root not found: {explicit_mlroot}")

    if explicit_matlab:
        exe = Path(explicit_matlab).resolve()
        if exe.exists():
            return exe.parent.parent
        raise SystemExit(f"MATLAB executable not found: {explicit_matlab}")

    fallback = Path(r"D:\Students\CYS\Matlab R2024b")
    if fallback.exists():
        return fallback
    raise SystemExit("MATLAB root not found. Pass --mlroot or --matlab.")


def matlab_executable(explicit_mlroot: str | None, explicit_matlab: str | None) -> Path:
    if explicit_matlab:
        exe = Path(explicit_matlab).resolve()
        if exe.exists():
            return exe
        raise SystemExit(f"MATLAB executable not found: {explicit_matlab}")

    root = matlab_root(explicit_mlroot, explicit_matlab)
    candidates = [
        root / "bin" / "matlab.exe",
        root / "bin" / "win64" / "matlab.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit(f"MATLAB executable not found under: {root}")


def matlab_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "''")


def matlab_path(value: Path) -> str:
    return str(value.resolve()).replace("\\", "/")


def codegen_save_path(save_path: Path) -> Path:
    if save_path.suffix.lower() not in {".m", ".java", ".vba"}:
        return save_path

    stem = save_path.stem
    cleaned = "".join(ch for ch in stem if ch.isalnum())
    if not cleaned:
        cleaned = "ModelExport"
    if not cleaned[0].isalpha():
        cleaned = f"Model{cleaned}"
    return save_path.with_name(f"{cleaned}{save_path.suffix}")


def build_runner(
    *,
    comsol_root: Path,
    script_path: Path | None,
    model_path: Path | None,
    save_path: Path | None,
    workdir: Path,
) -> Path:
    lines = [
        "try",
        f"cd('{matlab_quote(matlab_path(workdir))}');",
        f"addpath('{matlab_quote(matlab_path(comsol_root / 'mli'))}');",
        f"[port,pid] = mphstartcomsolmphserver('comsolpath','{matlab_quote(matlab_path(comsol_root))}','timeout',120);",
        "fprintf('COMSOL server port=%d pid=%d\\n', port, pid);",
        "mphstart(port);",
        f"workdir_path = '{matlab_quote(matlab_path(workdir))}';",
    ]
    if model_path is not None:
        lines += [
            f"model_path = '{matlab_quote(matlab_path(model_path))}';",
            "model = mphopen(model_path);",
        ]
    if script_path is not None:
        lines.append(f"run('{matlab_quote(matlab_path(script_path))}');")
    if save_path is not None:
        actual_save_path = codegen_save_path(save_path)
        lines.append(f"mphsave(model, '{matlab_quote(matlab_path(actual_save_path))}', 'copy', 'on');")
        if actual_save_path != save_path:
            lines.append(
                f"movefile('{matlab_quote(matlab_path(actual_save_path))}', '{matlab_quote(matlab_path(save_path))}', 'f');"
            )
    lines += [
        "import com.comsol.model.util.*;",
        "ModelUtil.disconnect;",
        "exit(0);",
        "catch ME",
        "disp(getReport(ME, 'extended'));",
        "try",
        "import com.comsol.model.util.*;",
        "ModelUtil.disconnect;",
        "catch",
        "end",
        "exit(1);",
        "end",
    ]
    tempdir = Path(tempfile.mkdtemp(prefix="codex-comsol-matlab-", dir=str(workdir)))
    runner = tempdir / "codex_comsol_batch_runner.m"
    runner.write_text("\n".join(lines), encoding="utf-8")
    return runner


def run_comsol_matlab(*, matlab_exe: Path, batch_script: Path, workdir: Path) -> None:
    command = [str(matlab_exe), "-batch", f"run('{matlab_path(batch_script)}')"]
    completed = subprocess.run(command, cwd=str(workdir), check=False, capture_output=True, text=True)  # noqa: S603
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)
        raise SystemExit(completed.returncode)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")


def run_script_command(args: argparse.Namespace) -> int:
    installation = detect_installation(args.root)
    comsol_root = Path(installation["root"])
    workdir = Path(args.cwd).resolve() if args.cwd else Path.cwd()
    batch_script = build_runner(
        comsol_root=comsol_root,
        script_path=Path(args.script).resolve(),
        model_path=Path(args.model).resolve() if args.model else None,
        save_path=Path(args.save).resolve() if args.save else None,
        workdir=workdir,
    )
    run_comsol_matlab(
        matlab_exe=matlab_executable(args.mlroot, args.matlab),
        batch_script=batch_script,
        workdir=workdir,
    )
    return 0


def convert_command(args: argparse.Namespace) -> int:
    installation = detect_installation(args.root)
    comsol_root = Path(installation["root"])
    workdir = Path(args.cwd).resolve() if args.cwd else Path.cwd()
    output = Path(args.output).resolve()
    batch_script = build_runner(
        comsol_root=comsol_root,
        script_path=None,
        model_path=Path(args.input).resolve(),
        save_path=output,
        workdir=workdir,
    )
    run_comsol_matlab(
        matlab_exe=matlab_executable(args.mlroot, args.matlab),
        batch_script=batch_script,
        workdir=workdir,
    )
    print(str(output))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run flexible COMSOL + MATLAB LiveLink workflows.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="Optional COMSOL installation root override.")
    common.add_argument("--matlab", help="Path to matlab.exe.")
    common.add_argument("--mlroot", help="MATLAB root directory.")
    common.add_argument("--cwd", help="Working directory.")

    run_script = subparsers.add_parser("run-script", parents=[common], help="Run a MATLAB .m file under COMSOL LiveLink.")
    run_script.add_argument("--script", required=True, help="Path to a MATLAB script.")
    run_script.add_argument("--model", help="Optional input .mph model to open into variable 'model'.")
    run_script.add_argument("--save", help="Optional output file path for mphsave(model, ...).")
    run_script.set_defaults(func=run_script_command)

    convert = subparsers.add_parser("convert", parents=[common], help="Open a model and save it as .mph, .m, or .java.")
    convert.add_argument("--input", required=True, help="Input .mph model.")
    convert.add_argument("--output", required=True, help="Output .mph, .m, or .java file.")
    convert.set_defaults(func=convert_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
