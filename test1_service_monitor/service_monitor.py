import json
import socket
import subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SERVICES = {
    "httpd": ["httpd"],
    "rabbitmq-server": ["rabbitmq-server", "rabbitmq"],
    "postgresql": ["postgresql", "postgresql-14", "postgresql-15"],
}


def run_command(command):
    """Run a shell command and return (return_code, stdout, stderr)."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_service_active(service_name: str) -> bool:
    """
    Check service state using systemctl first, then fall back to service command.
    """
    rc, stdout, _ = run_command(["systemctl", "is-active", service_name])
    if rc == 0 and stdout.lower() == "active":
        return True

    # Fallback for older systems
    rc, stdout, stderr = run_command(["service", service_name, "status"])
    combined = f"{stdout}\n{stderr}".lower()
    return rc == 0 or "running" in combined or "active (running)" in combined


def get_service_status(service_label: str, candidate_names):
    for candidate in candidate_names:
        try:
            if is_service_active(candidate):
                return "UP", candidate
        except FileNotFoundError:
            break
    return "DOWN", candidate_names[0]


def build_payload(service_name: str, service_status: str, host_name: str):
    return {
        "service_name": service_name,
        "service_status": service_status,
        "host_name": host_name,
        "@timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


def write_payload(payload):
    timestamp = payload["@timestamp"].replace(":", "-")
    file_name = f'{payload["service_name"]}-status-{timestamp}.json'
    file_path = OUTPUT_DIR / file_name
    with open(file_path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2)
    return file_path


def get_application_status(service_payloads):
    return "UP" if all(p["service_status"] == "UP" for p in service_payloads) else "DOWN"


def main():
    host_name = socket.gethostname()
    payloads = []

    for logical_name, candidate_names in SERVICES.items():
        status, detected_name = get_service_status(logical_name, candidate_names)
        payload = build_payload(
            service_name=logical_name,
            service_status=status,
            host_name=host_name,
        )
        payload["detected_service_name"] = detected_name
        path = write_payload(payload)
        payloads.append(payload)
        print(f"Wrote {path}")

    application_summary = {
        "application_name": "rbcapp1",
        "application_status": get_application_status(payloads),
        "host_name": host_name,
        "services": payloads,
        "@timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    summary_path = OUTPUT_DIR / f'rbcapp1-status-{application_summary["@timestamp"].replace(":", "-")}.json'
    with open(summary_path, "w", encoding="utf-8") as fp:
        json.dump(application_summary, fp, indent=2)
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
