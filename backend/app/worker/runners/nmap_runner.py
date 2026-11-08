import xml.etree.ElementTree as ET
from typing import Any, Dict, List
from app.core.logging import logger
from app.worker.runners.base import safe_subprocess_exec, validate_target_arg


def parse_nmap_xml(raw_xml: str) -> List[Dict[str, Any]]:
    """Parses standard Nmap XML output to extract open ports and detected services."""
    open_ports = []
    if not raw_xml or not raw_xml.strip():
        return open_ports

    try:
        root = ET.fromstring(raw_xml.strip())
        for host in root.findall("host"):
            status = host.find("status")
            if status is not None and status.get("state") != "up":
                continue

            ports_elem = host.find("ports")
            if ports_elem is None:
                continue

            for port in ports_elem.findall("port"):
                state_elem = port.find("state")
                if state_elem is not None and state_elem.get("state") == "open":
                    port_id = int(port.get("portid", 0))
                    protocol = port.get("protocol", "tcp")
                    service_elem = port.find("service")
                    service_name = service_elem.get("name", "unknown") if service_elem is not None else "unknown"

                    open_ports.append({
                        "port": port_id,
                        "protocol": protocol,
                        "state": "open",
                        "service": service_name,
                    })
    except ET.ParseError as e:
        logger.warning(f"Error parsing Nmap XML: {e}")

    return open_ports


async def run_nmap(target: str, timeout: int = 30) -> List[Dict[str, Any]]:
    """Runs unprivileged safe top-port scan against validated target."""
    clean_target = validate_target_arg(target)
    cmd = [
        "nmap",
        "-sT",              # Unprivileged TCP connect scan
        "-Pn",              # Skip ping check
        "--top-ports", "20",
        "-T3",              # Polite timing
        "--open",
        "-oX", "-",         # XML output to stdout
        clean_target,
    ]

    code, stdout, stderr = await safe_subprocess_exec(cmd, timeout_seconds=timeout)
    if code != 0 or not stdout:
        logger.info(f"nmap CLI returned code {code} or empty output.")
        return []

    return parse_nmap_xml(stdout)
