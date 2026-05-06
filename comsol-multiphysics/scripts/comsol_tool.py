#!/usr/bin/env python
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None


WINDOWS_COMMANDS = [
    "comsol",
    "comsolbatch",
    "comsolcompile",
    "comsolmethodexec",
    "comsolmphclient",
    "comsolmphserver",
    "comsolpowerpointbatch",
    "comsoldoc",
    "comsolxpl",
]

KNOWN_DOCS = [
    "ApplicationProgrammingGuide.pdf",
    "COMSOL_ApplicationBuilderManual.pdf",
    "COMSOL_PostprocessingAndVisualization.pdf",
    "COMSOL_ProgrammingReferenceManual.pdf",
    "COMSOL_ReferenceManual.pdf",
    "IntroductionToCOMSOLMultiphysics.pdf",
]


def normalize_root(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path.name.lower() == "win64" and path.parent.name.lower() == "bin":
        return path.parent.parent
    if path.name.lower() == "bin":
        return path.parent
    return path


def existing_path(path_str: str | None) -> Path | None:
    if not path_str:
        return None
    path = Path(path_str)
    if path.exists():
        return normalize_root(path)
    return None


def registry_roots() -> list[Path]:
    if winreg is None:
        return []

    locations = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\COMSOL\COMSOL64", "COMSOLROOT"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\COMSOL\COMSOL64", "COMSOLROOT"),
    ]
    roots: list[Path] = []

    for hive, subkey, value_name in locations:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
        except OSError:
            continue

        path = existing_path(value)
        if path is not None:
            roots.append(path)

    for hive, base_key in [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\COMSOL"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\COMSOL"),
    ]:
        try:
            with winreg.OpenKey(hive, base_key) as key:
                index = 0
                while True:
                    try:
                        child = winreg.EnumKey(key, index)
                    except OSError:
                        break
                    index += 1
                    try:
                        with winreg.OpenKey(hive, rf"{base_key}\{child}") as child_key:
                            value, _ = winreg.QueryValueEx(child_key, "COMSOLROOT")
                    except OSError:
                        continue
                    path = existing_path(value)
                    if path is not None:
                        roots.append(path)
        except OSError:
            continue

    return roots


def filesystem_roots() -> list[Path]:
    patterns = [
        r"C:\Program Files\COMSOL*\Multiphysics",
        r"C:\Program Files\COMSOL\COMSOL*\Multiphysics",
        r"C:\Program Files\COMSOL64\Multiphysics",
        r"D:\Program Files\COMSOL*\Multiphysics",
        r"D:\Program Files\COMSOL\COMSOL*\Multiphysics",
        r"D:\Students\CYS\Software\COMSOL*\Multiphysics",
    ]
    roots: list[Path] = []
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            path = Path(path)
            if path.exists():
                roots.append(normalize_root(path))
    return roots


def root_score(path: Path) -> tuple[int, str]:
    command_count = sum(command_path(path, name).exists() for name in WINDOWS_COMMANDS)
    return (command_count, str(path).lower())


def candidate_roots() -> list[Path]:
    candidates: list[Path] = []

    env_root = existing_path(os.environ.get("COMSOLROOT"))
    if env_root is not None:
        candidates.append(env_root)

    candidates.extend(registry_roots())

    standard_paths = [
        Path(r"C:\Program Files\COMSOL64\Multiphysics"),
        Path(r"C:\Program Files\COMSOL\Multiphysics"),
        Path(r"D:\Program Files\COMSOL\COMSOL62\Multiphysics"),
        Path(r"D:\Students\CYS\Software\COMSOL64\Multiphysics"),
    ]
    for path in standard_paths:
        if path.exists():
            candidates.append(normalize_root(path))

    candidates.extend(filesystem_roots())

    deduped: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            deduped.append(path)
            seen.add(key)

    return sorted(deduped, key=root_score, reverse=True)


def command_path(root: Path, command: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    if os.name == "nt":
        return root / "bin" / "win64" / f"{command}{suffix}"
    return root / "bin" / f"{command}{suffix}"


def detect_installation(explicit_root: str | None = None) -> dict:
    root = existing_path(explicit_root) if explicit_root else None
    if root is None:
        candidates = candidate_roots()
        if not candidates:
            raise SystemExit("No COMSOL installation detected. Set COMSOLROOT or pass --root.")
        root = candidates[0]

    if not root.exists():
        raise SystemExit(f"COMSOL root does not exist: {root}")

    commands = {}
    for name in WINDOWS_COMMANDS:
        path = command_path(root, name)
        commands[name] = {"path": str(path), "exists": path.exists()}

    docs_dir = root / "doc" / "pdf" / "COMSOL_Multiphysics"
    docs = [str(docs_dir / doc) for doc in KNOWN_DOCS if (docs_dir / doc).exists()]

    applications_root = root / "applications"
    application_modules = []
    if applications_root.exists():
        application_modules = sorted(
            [item.name for item in applications_root.iterdir() if item.is_dir()]
        )

    mli_root = root / "mli"
    mli_examples = []
    if mli_root.exists():
        for name in [
            "mphapplicationlibraries.m",
            "mphbatchinfo.m",
            "mpheval.m",
            "mphgeom.m",
        ]:
            candidate = mli_root / name
            if candidate.exists():
                mli_examples.append(str(candidate))

    version = None
    version_warning = None
    batch_exe = Path(commands["comsolbatch"]["path"])
    if batch_exe.exists():
        try:
            result = subprocess.run(
                [str(batch_exe), "-version"],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            version = (result.stdout or result.stderr).strip() or None
        except subprocess.TimeoutExpired:
            version_warning = "Timed out running comsolbatch -version after 20 seconds."
        except OSError:
            version_warning = "Failed to run comsolbatch -version."

    return {
        "root": str(root),
        "version": version,
        "version_warning": version_warning,
        "path_on_shell": any(shutil.which(name) for name in WINDOWS_COMMANDS),
        "commands": commands,
        "docs": docs,
        "applications_root": str(applications_root),
        "application_module_count": len(application_modules),
        "application_modules_sample": application_modules[:20],
        "mli_root": str(mli_root),
        "mli_present": mli_root.exists(),
        "mli_examples": mli_examples,
        "licenseinfo_ini": str(root / "licenseinfo.ini"),
        "license_dir": str(root / "license"),
    }


def run_command(command: list[str], dry_run: bool, detach: bool, cwd: str | None) -> int:
    printable = subprocess.list2cmdline(command)
    if dry_run:
        print(printable)
        return 0

    if detach:
        popen_kwargs: dict = {"cwd": cwd}
        if os.name == "nt":
            creationflags = 0
            creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)
            creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            creationflags |= getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            popen_kwargs["creationflags"] = creationflags
        proc = subprocess.Popen(command, **popen_kwargs)  # noqa: S603
        print(json.dumps({"status": "started", "pid": proc.pid, "command": printable}, indent=2))
        return 0

    completed = subprocess.run(command, cwd=cwd, check=False)  # noqa: S603
    return completed.returncode


def resolve_executable(root: str | None, command: str) -> str:
    installation = detect_installation(root)
    command_info = installation["commands"].get(command)
    if not command_info or not command_info["exists"]:
        raise SystemExit(f"Command not available: {command}")
    return command_info["path"]


def append_flag(args: list[str], flag: str, value: str | None) -> None:
    if value is None:
        return
    args.extend([flag, value])


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", help="Override the COMSOL installation root.")
    parser.add_argument("--cwd", help="Working directory to launch COMSOL from.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without running it.")


def add_detach_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--detach", action="store_true", help="Start the process detached.")


def cmd_discover(args: argparse.Namespace) -> int:
    print(json.dumps(detect_installation(args.root), indent=2))
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    installation = detect_installation(args.root)
    print(installation.get("version") or "Version unavailable")
    return 0


def cmd_help(args: argparse.Namespace) -> int:
    executable = resolve_executable(args.root, args.command_name)
    return run_command([executable, "-help"], args.dry_run, False, args.cwd)


def cmd_desktop(args: argparse.Namespace) -> int:
    executable = resolve_executable(args.root, "comsol")
    command = [executable]
    if args.target:
        command.append(args.target)
    command.extend(args.extra or [])
    return run_command(command, args.dry_run, args.detach, args.cwd)


def cmd_batch(args: argparse.Namespace) -> int:
    executable = resolve_executable(args.root, "comsolbatch")
    command = [executable]
    append_flag(command, "-inputfile", args.inputfile)
    append_flag(command, "-outputfile", args.outputfile)
    append_flag(command, "-outputdir", args.outputdir)
    append_flag(command, "-study", args.study)
    append_flag(command, "-batchlog", args.batchlog)
    append_flag(command, "-methodcall", args.methodcall)
    append_flag(command, "-methodinputfile", args.methodinputfile)
    append_flag(command, "-paramfile", args.paramfile)
    append_flag(command, "-pname", args.pname)
    append_flag(command, "-plist", args.plist)
    append_flag(command, "-pindex", args.pindex)
    if args.usebatchlic:
        command.append("-usebatchlic")
    if args.graphics:
        command.append("-graphics")
    command.extend(args.extra or [])
    return run_command(command, args.dry_run, False, args.cwd)


def cmd_server(args: argparse.Namespace) -> int:
    executable = resolve_executable(args.root, "comsolmphserver")
    command = [executable]
    append_flag(command, "-port", str(args.port) if args.port is not None else None)
    append_flag(command, "-portfile", args.portfile)
    if args.multi:
        command.extend(["-multi", "on"])
    if args.graphics:
        command.append("-graphics")
    command.extend(args.extra or [])
    return run_command(command, args.dry_run, args.detach, args.cwd)


def cmd_client(args: argparse.Namespace) -> int:
    executable = resolve_executable(args.root, "comsolmphclient")
    command = [executable]
    append_flag(command, "-host", args.host)
    append_flag(command, "-port", str(args.port) if args.port is not None else None)
    if args.target:
        command.append(args.target)
    command.extend(args.extra or [])
    return run_command(command, args.dry_run, args.detach, args.cwd)


def cmd_compile(args: argparse.Namespace) -> int:
    executable = resolve_executable(args.root, "comsolcompile")
    command = [executable, args.target]
    append_flag(command, "-outputdir", args.outputdir)
    append_flag(command, "-platforms", args.platforms)
    append_flag(command, "-runtimetype", args.runtimetype)
    command.extend(args.extra or [])
    return run_command(command, args.dry_run, False, args.cwd)


def cmd_exec(args: argparse.Namespace) -> int:
    executable = resolve_executable(args.root, args.command_name)
    command = [executable]
    command.extend(args.extra or [])
    return run_command(command, args.dry_run, args.detach, args.cwd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stable helper for local COMSOL operations.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    discover = subparsers.add_parser("discover", help="Detect the local COMSOL installation.")
    add_common_options(discover)
    discover.set_defaults(func=cmd_discover)

    version = subparsers.add_parser("version", help="Print the detected COMSOL version.")
    add_common_options(version)
    version.set_defaults(func=cmd_version)

    help_parser = subparsers.add_parser("help", help="Show launcher help for a specific COMSOL command.")
    add_common_options(help_parser)
    help_parser.add_argument("command_name", choices=WINDOWS_COMMANDS)
    help_parser.set_defaults(func=cmd_help)

    desktop = subparsers.add_parser("desktop", help="Launch COMSOL Desktop.")
    add_common_options(desktop)
    add_detach_option(desktop)
    desktop.add_argument("target", nargs="?", help="Optional model or application to open.")
    desktop.add_argument("extra", nargs=argparse.REMAINDER, help="Extra arguments passed through unchanged.")
    desktop.set_defaults(func=cmd_desktop)

    batch = subparsers.add_parser("batch", help="Run a COMSOL batch job.")
    add_common_options(batch)
    batch.add_argument("--inputfile", required=True, help="Input .mph or .class file.")
    batch.add_argument("--outputfile", help="Output .mph file.")
    batch.add_argument("--outputdir", help="Directory for related output files.")
    batch.add_argument("--study", help="Study tag to compute, for example std1.")
    batch.add_argument("--batchlog", help="File path for the batch log.")
    batch.add_argument("--methodcall", help="Method tag to run.")
    batch.add_argument("--methodinputfile", help="File with method inputs in name=value format.")
    batch.add_argument("--paramfile", help="Table file containing parameters for sweeps.")
    batch.add_argument("--pname", help="Comma-separated parameter names.")
    batch.add_argument("--plist", help="Comma-separated parameter values.")
    batch.add_argument("--pindex", help="Comma-separated parameter indices for output suffix control.")
    batch.add_argument("--usebatchlic", action="store_true", help="Request batch licenses.")
    batch.add_argument("--graphics", action="store_true", help="Display graphics while running.")
    batch.add_argument("extra", nargs=argparse.REMAINDER, help="Extra arguments passed through unchanged.")
    batch.set_defaults(func=cmd_batch)

    server = subparsers.add_parser("server", help="Start COMSOL Multiphysics Server.")
    add_common_options(server)
    add_detach_option(server)
    server.add_argument("--port", type=int, help="Server port.")
    server.add_argument("--portfile", help="Write the chosen port to this file.")
    server.add_argument("--multi", action="store_true", help="Accept repeated client connections.")
    server.add_argument("--graphics", action="store_true", help="Display graphics on the server.")
    server.add_argument("extra", nargs=argparse.REMAINDER, help="Extra arguments passed through unchanged.")
    server.set_defaults(func=cmd_server)

    client = subparsers.add_parser("client", help="Launch COMSOL client and connect to a server.")
    add_common_options(client)
    add_detach_option(client)
    client.add_argument("--host", help="Server host name.")
    client.add_argument("--port", type=int, help="Server port.")
    client.add_argument("target", nargs="?", help="Optional target to open after connecting.")
    client.add_argument("extra", nargs=argparse.REMAINDER, help="Extra arguments passed through unchanged.")
    client.set_defaults(func=cmd_client)

    compile_parser = subparsers.add_parser("compile", help="Compile Java model files or COMSOL applications.")
    add_common_options(compile_parser)
    compile_parser.add_argument("target", help="Path to a .java file, .mph application, or archive.")
    compile_parser.add_argument("--outputdir", help="Output directory for compiled artifacts.")
    compile_parser.add_argument("--platforms", help="Comma-separated platform list.")
    compile_parser.add_argument("--runtimetype", choices=["download", "embed"], help="Runtime packaging mode.")
    compile_parser.add_argument("extra", nargs=argparse.REMAINDER, help="Extra arguments passed through unchanged.")
    compile_parser.set_defaults(func=cmd_compile)

    exec_parser = subparsers.add_parser("exec", help="Run any detected COMSOL launcher directly.")
    add_common_options(exec_parser)
    add_detach_option(exec_parser)
    exec_parser.add_argument("command_name", choices=WINDOWS_COMMANDS)
    exec_parser.add_argument("extra", nargs=argparse.REMAINDER, help="Arguments passed through unchanged.")
    exec_parser.set_defaults(func=cmd_exec)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
