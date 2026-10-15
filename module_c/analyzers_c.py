import shutil
import subprocess
import tempfile
from pathlib import Path

CPPCHECK = shutil.which("cppcheck")
FLAWFINDER = shutil.which("flawfinder")
SEMGREP = shutil.which("semgrep")

TIMEOUT_SECONDS = 30


def run_command(command: list[str]) -> dict:
    """Run an analyzer command and capture its output."""

    try:
        result = subprocess.run(  # noqa: PLW1510
            command,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            errors="replace",
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Analyzer timed out.",
            "returncode": None,
        }

    except OSError as error:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(error),
            "returncode": None,
        }


def analyze_with_cppcheck(file_path: Path) -> dict:
    """Run Cppcheck and return its findings."""

    if not CPPCHECK:
        return {"success": False, "findings": "Cppcheck executable not found."}

    result = run_command([
        CPPCHECK,
        "--enable=warning,style,performance,portability",
        "--template={file}:{line}: {severity}: {message} [{id}]",
        str(file_path),
    ])

    findings = "\n".join(
        part for part in [result["stdout"], result["stderr"]] if part
    )

    return {
        "success": result["returncode"] == 0,
        "findings": findings or "No findings reported.",
    }


def analyze_with_flawfinder(file_path: Path) -> dict:
    """Run Flawfinder and return its findings."""

    if not FLAWFINDER:
        return {"success": False, "findings": "Flawfinder executable not found."}

    result = run_command([
        FLAWFINDER,
        "--quiet",
        str(file_path),
    ])

    findings = "\n".join(
        part for part in [result["stdout"], result["stderr"]] if part
    )

    return {
        "success": result["returncode"] is not None,
        "findings": findings or "No findings reported.",
    }


def analyze_with_semgrep(file_path: Path) -> dict:
    """Run Semgrep using its built-in security rules."""

    if not SEMGREP:
        return {"success": False, "findings": "Semgrep executable not found."}

    result = run_command([
        SEMGREP,
        "scan",
        "--config",
        "p/security-audit",
        "--json",
        "--quiet",
        str(file_path),
    ])

    if result["returncode"] is None:
        return {
            "success": False,
            "findings": result["stderr"],
        }

    try:
        import json

        report = json.loads(result["stdout"] or "{}")

        findings = []
        for item in report.get("results", []):
            findings.append(
                f"Rule: {item.get('check_id', 'unknown')}; "
                f"Line: {item.get('start', {}).get('line', '?')}; "
                f"Severity: {item.get('extra', {}).get('severity', 'unknown')}; "
                f"Message: {item.get('extra', {}).get('message', '')}"
            )

        errors = report.get("errors", [])

        if errors:
            findings.extend(
                f"Semgrep error: {item.get('message', str(item))}"
                for item in errors
            )

        return {
            "success": not errors,
            "findings": "\n".join(findings) or "No findings reported.",
        }

    except ValueError:
        return {
            "success": False,
            "findings": (
                "Could not parse Semgrep JSON output.\n"
                + result["stderr"]
            ),
        }


def analyze_code(code: str, language: str = "c") -> dict:
    """Run all three analyzers against a source-code snippet."""

    suffixes = {
        "c": ".c",
        "cpp": ".cpp",
        "c++": ".cpp",
    }

    suffix = suffixes.get(language.lower())

    if suffix is None:
        raise ValueError("language must be 'c' or 'cpp'.")

    if not code or not code.strip():
        raise ValueError("Source code must not be empty.")

    with tempfile.TemporaryDirectory(prefix="primevul_") as temp_dir:
        file_path = Path(temp_dir) / f"sample{suffix}"
        file_path.write_text(code, encoding="utf-8")

        results = {
            "cppcheck": analyze_with_cppcheck(file_path),
            "flawfinder": analyze_with_flawfinder(file_path),
            "semgrep": analyze_with_semgrep(file_path),
        }

    return results