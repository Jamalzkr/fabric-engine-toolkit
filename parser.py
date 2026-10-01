import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Severity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Error:
    message: str
    context: str = ""
    severity: Severity = Severity.WARNING
    count: int = 1


@dataclass
class Interface:
    name: str
    status: str
    protocol_status: str = ""
    speed: str = ""
    duplex: str = ""
    vlan: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class SystemInfo:
    model: str = ""
    uptime: str = ""
    version: str = ""
    serial: str = ""
    base_mac: str = ""
    license: str = ""
    enabled_features: List[str] = field(default_factory=list)


@dataclass
class vISTConfig:
    """vIST cluster configuration."""
    is_vist_member: bool = False
    vist_link_status: str = ""
    peer_ip: str = ""
    peer_name: str = ""
    mlt_status: str = ""
    sync_status: str = ""


@dataclass
class Metrics:
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    temperature: Optional[float] = None
    power_status: str = ""
    fan_status: str = ""


@dataclass
class ShowTechAnalysis:
    system_info: SystemInfo = field(default_factory=SystemInfo)
    errors: List[Error] = field(default_factory=list)
    warnings: List[Error] = field(default_factory=list)
    interfaces: List[Interface] = field(default_factory=list)
    metrics: Metrics = field(default_factory=Metrics)
    vlans: int = 0
    vrfs: int = 0
    arp_entries: int = 0
    down_ports: int = 0
    raw_sections: Dict[str, str] = field(default_factory=dict)
    vist_config: vISTConfig = field(default_factory=vISTConfig)


def parse_show_tech(text: str) -> ShowTechAnalysis:
    """Parse Show Fulltech output into structured data."""
    result = ShowTechAnalysis()

    # Extract device model from prompt
    result.system_info = extract_system_info(text)

    # Extract interfaces
    result.interfaces = extract_interfaces(text)

    # Count down ports
    result.down_ports = len([i for i in result.interfaces if i.status.lower() == 'down'])

    # Extract VRF, VLAN, and ARP counts from "show ip vrf" summary table
    vrf_section_match = re.search(r'(?i)show ip vrf.*?\n(.*?(?=Command:\[|$))', text, re.DOTALL)
    if vrf_section_match:
        vrf_section = vrf_section_match.group(1)

        # Look for the summary line with counts: "1         25        161       ..."
        summary_line_match = re.search(r'\n\s*(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+', vrf_section)
        if summary_line_match:
            result.vrfs = int(summary_line_match.group(1))
            result.vlans = int(summary_line_match.group(2))
            result.arp_entries = int(summary_line_match.group(3))
        else:
            # Fallback: try to count VRF entries from the data section
            vrf_lines = [line for line in vrf_section.split('\n') if line.strip() and not any(x in line for x in ['VRF', '---', 'COUNT'])]
            result.vrfs = max(0, len(vrf_lines) - 2) if vrf_lines else 0

    # If we still don't have VLAN count, try to extract from "show vlan" output
    if result.vlans == 0:
        vlan_section_match = re.search(r'(?i)show vlan\s+name.*?\n(.*?(?=Command:\[|$))', text, re.DOTALL)
        if vlan_section_match:
            vlan_section = vlan_section_match.group(1)
            vlan_lines = [line for line in vlan_section.split('\n') if line.strip() and re.match(r'^\d+\s+\d+\s+', line)]
            result.vlans = len(vlan_lines)

    # Extract errors and warnings
    result.errors, result.warnings = extract_errors_and_warnings(text, result.interfaces)

    # Extract vIST configuration
    result.vist_config = extract_vist_config(text)

    return result


def extract_system_info(text: str) -> SystemInfo:
    """Extract system information from prompt and commands."""
    info = SystemInfo()

    # Extract model from prompt (e.g., "BL-VSP4450-01:1#show fulltech")
    prompt_match = re.search(r'^([A-Za-z0-9\-]+):', text, re.MULTILINE)
    if prompt_match:
        info.model = prompt_match.group(1)

    # Extract version from "show boot config general" (e.g., "Version:        8.1.10.0")
    version_match = re.search(r'Version:\s*([0-9.]+)', text)
    if version_match:
        info.version = version_match.group(1).strip()

    # Extract uptime from "show sys-info" section
    uptime_match = re.search(r'SysUpTime\s*:\s*([^\n]+)', text)
    if uptime_match:
        info.uptime = uptime_match.group(1).strip()

    # Extract serial from "show sys-info" Chassis Info section
    serial_match = re.search(r'Serial#\s*:\s*([A-Z0-9]+)', text)
    if serial_match:
        info.serial = serial_match.group(1).strip()

    # Extract base MAC from Chassis Info section
    base_mac_match = re.search(r'BaseMacAddr\s*:\s*([0-9a-f:]+)', text)
    if base_mac_match:
        info.base_mac = base_mac_match.group(1).strip()

    # Extract license info from "show license" section
    if 'No license file is loaded' in text and 'Trial license expired' in text:
        info.license = "Base (Trial Expired)"
    elif 'No license file is loaded' in text:
        info.license = "Base"
    elif 'Premier license' in text:
        info.license = "Premier"
    else:
        info.license = "Unknown"

    # Extract enabled features by looking for show commands and boot config
    features = []
    feature_patterns = {
        'CFM': r'Command:\[\d+\]\s+\[\s*show\s+cfm',
        'EAPOL': r'Command:\[\d+\]\s+\[\s*show\s+eapol',
        'ISIS': r'Command:\[\d+\]\s+\[\s*show\s+ip\s+isis',
        'MLT': r'Command:\[\d+\]\s+\[\s*show\s+.*mlt',
        'NTP': r'Command:\[\d+\]\s+\[\s*show\s+ntp',
        'RADIUS': r'Command:\[\d+\]\s+\[\s*show\s+radius',
        'SMLT': r'Command:\[\d+\]\s+\[\s*show\s+.*smlt',
        'SPBM': r'Command:\[\d+\]\s+\[\s*show\s+.*spbm',
        'SSHD': r'boot\s+config\s+flags\s+sshd',
        'SYSLOG': r'Command:\[\d+\]\s+\[\s*show\s+(?:logging|syslog)',
        'VIST': r'(?:VIST\s+byPort|match-network\s*:\s*VIST|List\s+\d+\s+VIST)',
        'VRRP': r'Command:\[\d+\]\s+\[\s*show\s+ip\s+vrrp',
        'WEB': r'Command:\[\d+\]\s+\[\s*show\s+web'
    }

    for feature, pattern in feature_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            features.append(feature)

    info.enabled_features = sorted(features)

    return info


def extract_interfaces(text: str) -> List[Interface]:
    """Extract interface information from 'show interfaces gigabitEthernet' output."""
    interfaces = []

    # Look for the Port Interface section from "show interfaces gigabitEthernet" command
    interface_section = re.search(
        r'show interfaces gigabitEthernet\s*\].*?Port Interface.*?\n(.*?(?=Command:\[|$))',
        text,
        re.DOTALL | re.IGNORECASE
    )

    if not interface_section:
        return interfaces

    section_text = interface_section.group(1)
    lines = section_text.split('\n')

    for line in lines:
        # Skip header lines and empty lines
        if not line.strip() or '===' in line or 'PORT' in line or 'NUM' in line or '---' in line or 'DESCRIPTION' in line:
            continue

        # Parse interface line
        # Format: "1/1      192   1000BaseTX          true  false    1950  b4:47:5e:3b:c5:00 up     up"
        match = re.search(
            r'(\d+/\d+)\s+(\d+)\s+(\S+)\s+(\w+)\s+(\w+)\s+(\d+)\s+([0-9a-f:]+)\s+(\w+)\s+(\w+)',
            line
        )

        if match:
            port_num = match.group(1)
            description = match.group(3)
            admin_status = match.group(8)
            operate_status = match.group(9)

            iface = Interface(
                name=f"Port-{port_num}",
                status=operate_status,
                protocol_status=admin_status,
                speed=description if description != 'N/A' else ""
            )

            # Add warnings for down interfaces
            if iface.status.lower() == 'down':
                iface.warnings.append('Interface is down')

            interfaces.append(iface)

    return interfaces


def extract_errors_and_warnings(text: str, interfaces: List[Interface]) -> tuple[List[Error], List[Error]]:
    """Extract errors and warnings."""
    errors = []
    warnings = []

    # Group all down interfaces into a single warning
    down_interfaces = [iface.name for iface in interfaces if iface.status.lower() == 'down']
    if down_interfaces:
        # Format as comma-separated list
        down_list = ', '.join(down_interfaces)
        warnings.append(Error(
            message=f"Down Interfaces: {down_list}",
            severity=Severity.WARNING,
            count=len(down_interfaces)
        ))

    # Look for alarms in the alarm database
    alarm_section = re.search(r'show alarm database.*?(?=Command:|$)', text, re.DOTALL | re.IGNORECASE)
    if alarm_section:
        # Extract alarm lines
        for line in alarm_section.group(0).split('\n'):
            if 'License' in line or 'Link Down' in line or 'error' in line.lower():
                if 'License' in line:
                    warnings.append(Error(
                        message=line.strip(),
                        severity=Severity.WARNING
                    ))
                elif 'Link Down' in line:
                    warnings.append(Error(
                        message=line.strip(),
                        severity=Severity.WARNING
                    ))

    # Remove duplicates
    errors = list({e.message: e for e in errors}.values())
    warnings = list({w.message: w for w in warnings}.values())

    return errors, warnings


def extract_vist_config(text: str) -> vISTConfig:
    """Extract vIST cluster configuration from 'show virtual-ist' output."""
    config = vISTConfig()

    # Look for "show virtual-ist" command output
    vist_section = re.search(r'show virtual-ist.*?IST Info.*?\n(.*?)(?=Command:|$)', text, re.DOTALL | re.IGNORECASE)

    if vist_section:
        config.is_vist_member = True
        section_text = vist_section.group(1)

        # Parse the IST Info table
        # Format: PEER-IP ADDRESS | VLAN ID | ENABLE IST | IST STATUS
        lines = section_text.split('\n')

        for line in lines:
            # Skip header and separator lines
            if '----' in line or 'PEER-IP' in line or 'ADDRESS' in line or not line.strip():
                continue

            # Parse data line: "10.40.254.2          3888     true     up"
            parts = line.split()
            if len(parts) >= 4:
                try:
                    # Extract peer IP
                    if re.match(r'\d+\.\d+\.\d+\.\d+', parts[0]):
                        config.peer_ip = parts[0]

                    # Extract IST status (usually the 4th or later field)
                    for part in parts[3:]:
                        if part.lower() == 'up':
                            config.vist_link_status = 'up'
                        elif part.lower() == 'down':
                            config.vist_link_status = 'down'
                except:
                    pass

        # Parse IST STATE and MASTER/SLAVE info
        # Format: v6.0         Up                               Slave
        dialect_match = re.search(r'v[\d.]+\s+(Up|Down)\s+(Master|Slave)', section_text, re.IGNORECASE)
        if dialect_match:
            state = dialect_match.group(1).lower()
            role = dialect_match.group(2).lower()

            if state == 'up':
                config.sync_status = 'synced'
            else:
                config.sync_status = 'out-of-sync'

            config.peer_name = role.capitalize()

        # Check for SMLT/MLT configuration
        if 'SMLT' in text:
            config.mlt_status = 'SMLT'
        elif 'MLT' in text:
            config.mlt_status = 'MLT'

    return config
