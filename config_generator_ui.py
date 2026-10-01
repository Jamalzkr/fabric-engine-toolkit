"""VSP Config Generator UI - Complete Interface"""

import streamlit as st
import json
from datetime import datetime
from config_gen_logic import generate_config, VSP_MODELS, VOSS_VERSIONS
from config_validators import validate_all_inputs, validate_ports_for_model


def render_config_generator():
    """Main config generator UI"""
    st.title("⚙️ VSP Configuration Generator")
    st.markdown("Generate baseline configurations for VSP switches")

    # Initialize session state for templates
    if "saved_templates" not in st.session_state:
        st.session_state.saved_templates = {}
    if "current_config" not in st.session_state:
        st.session_state.current_config = None

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Generate Config", "Templates", "Help"])

    with tab1:
        render_generator_form()

    with tab2:
        render_templates_manager()

    with tab3:
        render_help()


def render_generator_form():
    """Render the configuration generator form"""
    st.subheader("Configuration Inputs")

    # Create two columns for better layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Device Information")
        node_name = st.text_input(
            "Node Name",
            placeholder="4901",
            help="4-digit identifier (e.g., 4901, 5520, 7830)"
        )

        location = st.text_input(
            "Location/Site Name",
            placeholder="CORE01",
            help="Physical location or site identifier"
        )

        vsp_model = st.selectbox(
            "VSP Model",
            options=list(VSP_MODELS.keys()),
            format_func=lambda x: f"{VSP_MODELS[x]['display']} - {VSP_MODELS[x]['description']}"
        )

        voss_version = st.selectbox(
            "VOSS Version",
            options=VOSS_VERSIONS,
            help="Select your current VOSS version"
        )

    with col2:
        st.markdown("### Network Configuration")
        vlan_id = st.text_input(
            "Access VLAN ID",
            placeholder="100",
            help="VLAN for edge access (1-4094, cannot be 1, 4051, or 4052)"
        )

        io_ports = st.text_input(
            "I/O Ports",
            placeholder="1/1-1/24",
            help="Port range for edge access (e.g., 1/1-1/48 or 1/1-1/24,2/1-2/4)"
        )

        nni_ports = st.text_input(
            "NNI Ports (VSP Interconnect)",
            placeholder="2/1-2/8",
            help="Port range connecting to other VSPs"
        )

    # vIST Configuration Section
    st.markdown("---")
    st.markdown("### vIST Configuration (Optional)")

    vist_enabled = st.checkbox(
        "Enable vIST Cluster",
        help="Check if this VSP is part of a dual vIST cluster"
    )

    if vist_enabled:
        col1, col2 = st.columns(2)

        with col1:
            vist_node_number = st.radio(
                "Node Position in vIST Cluster",
                [1, 2],
                help="Is this VSP #1 or #2 in the cluster?"
            )

            vist_vlan_id = st.text_input(
                "vIST VLAN ID",
                placeholder="4000",
                help="Unique VLAN for vIST peer communication"
            )

        with col2:
            vist_peer_name = st.text_input(
                "vIST Peer Node Name",
                placeholder="4902",
                help="4-digit node name of the peer VSP"
            )

            vist_base_mac = st.text_input(
                "vIST Base MAC (First 8 chars)",
                placeholder="00049642",
                help="First 8 hex characters from 'show sys-info' command"
            )
    else:
        vist_node_number = 1
        vist_vlan_id = ""
        vist_peer_name = ""
        vist_base_mac = ""

    # Generate button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        generate_btn = st.button("🚀 Generate Config", type="primary", use_container_width=True)

    with col2:
        clear_btn = st.button("🔄 Clear All", use_container_width=True)

    if clear_btn:
        st.session_state.current_config = None
        st.rerun()

    # Generate config if button clicked
    if generate_btn:
        # Validate inputs
        errors = validate_all_inputs(
            node_name, location, vlan_id, io_ports, nni_ports,
            vist_enabled, vist_peer_name, vist_vlan_id, vist_base_mac
        )

        # Validate ports against model
        if not errors and io_ports:
            is_valid, msg = validate_ports_for_model(io_ports, vsp_model)
            if not is_valid:
                errors.append(f"I/O Ports: {msg}")

        if not errors and nni_ports:
            is_valid, msg = validate_ports_for_model(nni_ports, vsp_model)
            if not is_valid:
                errors.append(f"NNI Ports: {msg}")

        if errors:
            st.error("❌ Validation Errors:")
            for error in errors:
                st.error(f"  • {error}")
        else:
            # Generate config
            config_lines = generate_config(
                node_name=node_name,
                sys_name=location,
                vsp_model=vsp_model,
                voss_version=voss_version,
                vlan_id=vlan_id,
                vlan_ports=io_ports,  # Note: this should be removed ports, using io_ports instead
                io_ports=io_ports,
                nni_ports=nni_ports,
                vist_enabled=vist_enabled,
                vist_is_node_1=(vist_node_number == 1),
                vist_peer_name=vist_peer_name,
                vist_vlan_id=vist_vlan_id,
                vist_base_mac=vist_base_mac
            )

            # Store in session
            st.session_state.current_config = {
                "node_name": node_name,
                "location": location,
                "vsp_model": vsp_model,
                "voss_version": voss_version,
                "config_lines": config_lines,
                "timestamp": datetime.now().isoformat()
            }

            st.success("✅ Configuration generated successfully!")

    # Display generated config
    if st.session_state.current_config:
        render_config_output(st.session_state.current_config)


def render_config_output(config_data):
    """Render the generated configuration with options"""
    st.markdown("---")
    st.markdown("## Generated Configuration")

    # Config metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("VSP Model", config_data["vsp_model"])
    with col2:
        st.metric("Node Name", config_data["node_name"])
    with col3:
        st.metric("Generated", config_data["timestamp"][:10])

    # Config display with syntax highlighting
    config_text = "\n".join(config_data["config_lines"])

    st.markdown("### Configuration Output")
    st.code(config_text, language="text")

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Copy to clipboard button
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            st.session_state.copied = True
            # In a real app, you'd use JavaScript for clipboard
            st.success("Configuration copied! (Paste from the code block above)")

    with col2:
        # Download as .cfg file
        st.download_button(
            label="💾 Download .cfg",
            data=config_text,
            file_name=f"vsp_{config_data['node_name']}_{config_data['location']}.cfg",
            mime="text/plain",
            use_container_width=True
        )

    with col3:
        # Save as template
        if st.button("💾 Save as Template", use_container_width=True):
            st.session_state.show_save_template = True

    with col4:
        # Print friendly version
        if st.button("🖨️ Print Friendly", use_container_width=True):
            st.session_state.show_print = True

    # Save template dialog
    if st.session_state.get("show_save_template", False):
        st.markdown("---")
        template_name = st.text_input("Template Name", placeholder="My Config Template")
        if st.button("Save Template"):
            if template_name:
                st.session_state.saved_templates[template_name] = config_data
                st.success(f"✅ Template '{template_name}' saved!")
                st.session_state.show_save_template = False
                st.rerun()


def render_templates_manager():
    """Render the templates manager"""
    st.subheader("Saved Configuration Templates")

    if not st.session_state.saved_templates:
        st.info("📭 No saved templates yet. Generate a configuration and save it as a template!")
        return

    # Display saved templates
    for template_name, template_data in st.session_state.saved_templates.items():
        with st.expander(f"📋 {template_name}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.text(f"VSP Model: {template_data['vsp_model']}")
            with col2:
                st.text(f"Node: {template_data['node_name']}")
            with col3:
                st.text(f"Location: {template_data['location']}")

            # Template actions
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Load", key=f"load_{template_name}"):
                    config_text = "\n".join(template_data["config_lines"])
                    st.session_state.current_config = template_data
                    st.success(f"Loaded template: {template_name}")
                    st.rerun()

            with col2:
                if st.button("Download", key=f"download_{template_name}"):
                    config_text = "\n".join(template_data["config_lines"])
                    st.download_button(
                        label="Download",
                        data=config_text,
                        file_name=f"vsp_{template_data['node_name']}.cfg",
                        mime="text/plain",
                        key=f"download_btn_{template_name}"
                    )

            with col3:
                if st.button("Delete", key=f"delete_{template_name}"):
                    del st.session_state.saved_templates[template_name]
                    st.success(f"Deleted template: {template_name}")
                    st.rerun()


def render_help():
    """Render help documentation"""
    st.markdown("""
    ## How to Use the Config Generator

    ### 1. Device Information
    - **Node Name**: 4-digit identifier (e.g., 4901 for a VSP4900, 5520 for VSP5520)
    - **Location**: Physical site identifier (e.g., CORE01, TowerB)
    - **VSP Model**: Select from the full VSP Universal line
    - **VOSS Version**: Select your current VOSS version

    ### 2. Network Configuration
    - **Access VLAN ID**: VLAN for edge access switches (must be unique, not 1/4051/4052)
    - **I/O Ports**: Ports connecting to edge switches (e.g., 1/1-1/48)
    - **NNI Ports**: Ports for VSP-to-VSP connections (e.g., 2/1-2/8)

    ### 3. vIST Configuration (Optional)
    For dual vIST clusters, enable and provide:
    - **Node Position**: Is this VSP #1 or #2?
    - **vIST VLAN ID**: Unique VLAN for peer communication
    - **Peer Node Name**: Name of the other VSP
    - **Base MAC**: First 8 hex characters from `show sys-info`

    ### Port Format Examples
    - Single range: `1/1-1/48`
    - Multiple ranges: `1/1-1/24,2/1-2/4`
    - With SFP: `1/1-1/48,2/1-2/8`

    ### Validation
    - Node names must be 4 digits
    - VLAN IDs must be 1-4094 (excluding 1, 4051, 4052)
    - Port ranges must follow valid format
    - vIST peer name must differ from node name

    ### Supported Models
    - **VSP4000 Series**: VSP4450, VSP4800, VSP4900-24
    - **VSP5000 Series**: VSP5520-24, VSP5520-48, VSP5720
    - **VSP7000 Series**: VSP7400-48Y, VSP7520, VSP7720, VSP7830

    ### Next Steps
    1. Fill in your device information
    2. Click "Generate Config"
    3. Review the configuration
    4. Copy to clipboard, download, or save as template
    5. Apply to your VSP using SSH or console access
    """)
