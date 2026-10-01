"""Input validation for config generator"""

import re


def validate_node_name(node_name: str) -> tuple[bool, str]:
    """Validate node name format (typically 4 digits)"""
    if not node_name:
        return False, "Node name is required"
    if not re.match(r'^\d{4}$', node_name):
        return False, "Node name should be 4 digits (e.g., '4901')"
    return True, ""


def validate_location(location: str) -> tuple[bool, str]:
    """Validate location/system name"""
    if not location:
        return False, "Location is required"
    if len(location) > 20:
        return False, "Location should be 20 characters or less"
    return True, ""


def validate_vlan_id(vlan_id: str) -> tuple[bool, str]:
    """Validate VLAN ID (1-4094)"""
    try:
        vlan_num = int(vlan_id)
        if vlan_num < 1 or vlan_num > 4094:
            return False, "VLAN ID must be between 1 and 4094"
        # Check reserved VLANs
        if vlan_num in [1, 4051, 4052]:
            return False, f"VLAN {vlan_num} is reserved"
        return True, ""
    except ValueError:
        return False, "VLAN ID must be a number"


def validate_port_range(port_range: str) -> tuple[bool, str]:
    """Validate port range format (e.g., 1/1-1/48 or 1/1-1/24,2/1-2/4)"""
    if not port_range:
        return False, "Port range is required"

    # Allow formats like: 1/1-1/48 or 1/1-1/24,2/1-2/4
    pattern = r'^(\d+/\d+-\d+/\d+)(,\d+/\d+-\d+/\d+)*$'
    if not re.match(pattern, port_range):
        return False, "Invalid port range format. Use: 1/1-1/48 or 1/1-1/24,2/1-2/4"

    return True, ""


def parse_port_range(port_range_str: str) -> list[tuple[int, int, int, int]]:
    """Parse port range string into list of (start_slot, start_port, end_slot, end_port) tuples"""
    ranges = []
    for range_part in port_range_str.split(','):
        match = re.match(r'^(\d+)/(\d+)-(\d+)/(\d+)$', range_part)
        if match:
            ranges.append((int(match.group(1)), int(match.group(2)),
                          int(match.group(3)), int(match.group(4))))
    return ranges


def validate_ports_for_model(port_range: str, model: str) -> tuple[bool, str]:
    """Validate that ports exist on the selected VSP model"""
    from config_gen_logic import VSP_MODELS

    if model not in VSP_MODELS:
        return False, f"Unknown model: {model}"

    model_ports = VSP_MODELS[model]['ports']
    # Parse model's available ports (format: "1/1-1/50" or "1/1-1/24,2/1-2/4")
    model_ranges = parse_port_range(model_ports)

    # Parse user's requested ports
    user_ranges = parse_port_range(port_range)

    for user_start_slot, user_start_port, user_end_slot, user_end_port in user_ranges:
        # Check if user's range falls within model's available ports
        valid = False
        for model_start_slot, model_start_port, model_end_slot, model_end_port in model_ranges:
            # Both ranges must be in the same slot pair
            if (user_start_slot == model_start_slot and user_end_slot == model_end_slot):
                # Check if user's ports fall within model's ports
                if (user_start_port >= model_start_port and user_end_port <= model_end_port):
                    valid = True
                    break

        if not valid:
            return False, f"Port {user_start_slot}/{user_start_port}-{user_end_slot}/{user_end_port} exceeds {model}'s available ports ({model_ports})"

    return True, ""


def validate_mac_address(mac: str) -> tuple[bool, str]:
    """Validate MAC address (8 hex characters)"""
    if not mac:
        return False, "Base MAC is required"
    if not re.match(r'^[0-9a-fA-F]{8}$', mac):
        return False, "Base MAC should be 8 hexadecimal characters (e.g., 00049642)"
    return True, ""


def validate_vist_peer_name(peer_name: str) -> tuple[bool, str]:
    """Validate vIST peer node name"""
    if not peer_name:
        return False, "Peer node name is required for vIST"
    if not re.match(r'^\d{4}$', peer_name):
        return False, "Peer node name should be 4 digits"
    return True, ""


def validate_all_inputs(node_name: str, location: str, vlan_id: str, io_ports: str,
                       nni_ports: str, vist_enabled: bool = False, vist_peer_name: str = "",
                       vist_vlan_id: str = "", vist_base_mac: str = "") -> list[str]:
    """Validate all inputs and return list of errors"""
    errors = []

    # Basic validation
    is_valid, msg = validate_node_name(node_name)
    if not is_valid:
        errors.append(msg)

    is_valid, msg = validate_location(location)
    if not is_valid:
        errors.append(msg)

    is_valid, msg = validate_vlan_id(vlan_id)
    if not is_valid:
        errors.append(f"Access VLAN: {msg}")

    is_valid, msg = validate_port_range(io_ports)
    if not is_valid:
        errors.append(f"I/O Ports: {msg}")

    is_valid, msg = validate_port_range(nni_ports)
    if not is_valid:
        errors.append(f"NNI Ports: {msg}")

    # vIST validation if enabled
    if vist_enabled:
        is_valid, msg = validate_vist_peer_name(vist_peer_name)
        if not is_valid:
            errors.append(f"vIST Peer: {msg}")

        is_valid, msg = validate_vlan_id(vist_vlan_id)
        if not is_valid:
            errors.append(f"vIST VLAN: {msg}")

        is_valid, msg = validate_mac_address(vist_base_mac)
        if not is_valid:
            errors.append(f"vIST Base MAC: {msg}")

        # Check if peer and node names are different
        if vist_peer_name == node_name:
            errors.append("Peer node name must be different from node name")

    return errors
