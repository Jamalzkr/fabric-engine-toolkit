"""VSP Configuration Generation Logic - Supports Universal Line"""

# VSP Model Specifications
VSP_MODELS = {
    "VSP4450": {
        "display": "VSP4450",
        "ports": "1/1-1/50",
        "description": "48-port + 2 management"
    },
    "VSP4800": {
        "display": "VSP4800",
        "ports": "1/1-1/50",
        "description": "48-port + 2 management"
    },
    "VSP4900-24": {
        "display": "VSP4900-24",
        "ports": "1/1-1/24,2/1-2/4",
        "description": "24-port Gigabit"
    },
    "VSP5520-24": {
        "display": "VSP5520-24",
        "ports": "1/1-1/24,2/1-2/4",
        "description": "24-port Gigabit"
    },
    "VSP5520-48": {
        "display": "VSP5520-48",
        "ports": "1/1-1/48,2/1-2/4",
        "description": "48-port Gigabit"
    },
    "VSP5720": {
        "display": "VSP5720",
        "ports": "1/1-1/48,2/1-2/8",
        "description": "48-port Gigabit + 8 SFP"
    },
    "VSP7400-48Y": {
        "display": "VSP7400-48Y",
        "ports": "1/1-1/48,2/1-2/8",
        "description": "48-port 10G"
    },
    "VSP7520": {
        "display": "VSP7520",
        "ports": "1/1-1/48,2/1-2/8",
        "description": "48-port 10G + 8 SFP"
    },
    "VSP7720": {
        "display": "VSP7720",
        "ports": "1/1-1/48,2/1-2/8",
        "description": "48-port 10G + 8 SFP"
    },
    "VSP7830": {
        "display": "VSP7830",
        "ports": "1/1-1/48,2/1-2/8",
        "description": "48-port 10G + 8 SFP"
    }
}

VOSS_VERSIONS = [
    "8.1 / 7.1 or older",
    "8.2.X",
    "8.3.X - 9.0.X",
    "9.1.X - 9.4.X"
]


def generate_config(node_name, sys_name, vsp_model, voss_version, vlan_id, vlan_ports, io_ports, nni_ports,
                   vist_enabled=False, vist_is_node_1=True, vist_peer_name="", vist_vlan_id="", vist_base_mac=""):
    """Generate VSP baseline configuration"""

    config_lines = []

    # Basic setup
    config_lines.append("en")
    config_lines.append("conf t")
    config_lines.append("boot config flags rlogind")
    config_lines.append("boot config flags telnetd")
    config_lines.append("ssh pass-auth")
    config_lines.append("ssh")
    config_lines.append("boot config flags ssh")
    config_lines.append("spbm")
    config_lines.append(f"prompt {node_name}")

    # ISIS and system config
    config_lines.append("router isis")
    config_lines.append("no router isis")
    config_lines.append("Yes")
    config_lines.append("router isis")
    config_lines.append(f"sys-name {node_name}_{sys_name}")
    config_lines.append(f"system-id 0000.0001.{node_name}")

    # SPBM config
    config_lines.append("spbm 1")
    # Format nick-name with first 4 characters of node name
    nick_part = f"{node_name[0]}{node_name[1]}{node_name[2]}{node_name[3]}" if len(node_name) >= 4 else node_name
    config_lines.append(f"spbm 1 nick-name 0.{nick_part}.00")
    config_lines.append("spbm 1 b-vid 4051-4052 primary 4051")
    config_lines.append("spbm 1 multicast enable")
    config_lines.append("spbm 1 ip enable")
    config_lines.append("manual-area 49.0001")

    # BVLANs
    config_lines.append("vlan create 4051 name BVLAN-1 type spbm-bvlan")
    config_lines.append("vlan create 4052 name BVLAN-2 type spbm-bvlan")

    # vIST configuration if enabled
    if vist_enabled:
        config_lines.append(f"vlan create {vist_vlan_id} name IST_vlan type port-mstprstp 0")
        config_lines.append(f"vlan i-sid {vist_vlan_id} {vist_vlan_id}")
        config_lines.append(f"interface vlan {vist_vlan_id}")

        # Set IP based on node number
        node_ip_octet = "1" if vist_is_node_1 else "2"
        config_lines.append(f"ip address 172.20.{vist_vlan_id}.{node_ip_octet}/30")

        # SMLT BMAC
        bmac_str = f"{vist_base_mac[0]}{vist_base_mac[1]}:{vist_base_mac[2]}{vist_base_mac[3]}:{vist_base_mac[4]}{vist_base_mac[5]}:{vist_base_mac[6]}{vist_base_mac[7]}:FF:FF"
        config_lines.append(f"spbm 1 smlt-virtual-bmac {bmac_str}")
        config_lines.append(f"spbm 1 smlt-peer-system-id 0000.0001.{vist_peer_name}")

        # vIST peer IP
        peer_ip_octet = "2" if vist_is_node_1 else "1"
        config_lines.append(f"virtual-ist peer-ip 172.20.{vist_vlan_id}.{peer_ip_octet} vlan {vist_vlan_id}")

    # Common config
    config_lines.append("cfm spbm en")
    config_lines.append(f"vlan member remove 1 {vlan_ports}")

    # Loopback and ISIS
    config_lines.append("interface loopback 1")
    # Extract octets for IP
    octet_part = f"{node_name[0]}{node_name[1]}.{node_name[2]}{node_name[3]}" if len(node_name) >= 4 else f"00.{node_name}"
    config_lines.append(f"ip address 1 172.17.{octet_part}/32")

    config_lines.append("router isis")
    config_lines.append(f"ip-source-address 172.17.{octet_part}")
    config_lines.append("spbm 1 ip en")
    config_lines.append("router isis")
    config_lines.append("redistribute direct")
    config_lines.append("redistribute direct enable")
    config_lines.append("router isis")
    config_lines.append("router isis enable")
    config_lines.append("exit")
    config_lines.append("isis apply redistribute direct")
    config_lines.append("conf t")

    # Management
    config_lines.append("mgmt clip")
    config_lines.append(f"ip address 172.16.{octet_part}/32")
    config_lines.append("enable")

    # VLAN configuration
    config_lines.append(f"vlan create {vlan_id} type port-mstprstp 0")
    config_lines.append(f"vlan i-sid {vlan_id} {vlan_id}")
    config_lines.append(f"interface vlan {vlan_id}")
    config_lines.append(f"ip address 10.{vlan_id}.1.1/24")
    config_lines.append("ip spb-multicast enable")
    config_lines.append(f"vlan members add {vlan_id} {io_ports}")

    # IO Ports configuration
    config_lines.append(f"interface gigabitEthernet {io_ports}")
    config_lines.append("no spanning-tree mstp force-port-state enable")
    config_lines.append("y")
    config_lines.append("no shut")

    # NNI Ports configuration
    config_lines.append(f"interface gigabitEthernet {nni_ports}")
    config_lines.append("isis")
    config_lines.append("isis spbm 1")
    config_lines.append("isis en")
    config_lines.append("no spanning-tree mstp force-port-state enable")
    config_lines.append("y")
    config_lines.append("untagged-frames-discard")
    config_lines.append("no shut")

    return config_lines
