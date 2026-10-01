"""Native Streamlit dashboard (no iframe)."""
import streamlit as st
from parser import ShowTechAnalysis
from typing import List, Dict
from best_practices import validate_best_practices
import re
import difflib


def get_diff_html(text1: str, text2: str, max_lines: int = 50) -> str:
    """Generate colored diff between two texts."""
    lines1 = text1.split('\n')[:max_lines]
    lines2 = text2.split('\n')[:max_lines]

    diff = list(difflib.unified_diff(lines1, lines2, lineterm='', n=1))

    if len(diff) <= 2:  # Only header lines, no differences
        return '<span style="color: #06a77d; font-weight: bold;">✓ Outputs are identical</span>'

    html_lines = []
    for line in diff[2:]:  # Skip unified diff headers
        if line.startswith('+'):
            html_lines.append(f'<div style="color: #06a77d; background-color: rgba(6, 167, 125, 0.15); padding: 4px; margin: 2px 0; font-family: monospace; border-left: 3px solid #06a77d;">+ {line[1:]}</div>')
        elif line.startswith('-'):
            html_lines.append(f'<div style="color: #e63946; background-color: rgba(230, 57, 70, 0.15); padding: 4px; margin: 2px 0; font-family: monospace; border-left: 3px solid #e63946;">- {line[1:]}</div>')
        elif line.startswith('@@'):
            html_lines.append(f'<div style="color: #fcbf49; font-style: italic; padding: 4px; margin: 8px 0 4px 0; font-family: monospace;">{line}</div>')
        else:
            html_lines.append(f'<div style="color: #d1d5db; padding: 2px; margin: 2px 0; font-family: monospace;">  {line}</div>')

    html = '<div style="background-color: #1a1a1a; padding: 12px; border-radius: 5px; overflow-x: auto; max-height: 600px; overflow-y: auto;">'
    html += '\n'.join(html_lines[:100])
    if len(html_lines) > 100:
        html += f'<div style="color: #fcbf49; padding: 8px; margin-top: 8px;">... ({len(html_lines) - 100} more differences)</div>'
    html += '</div>'
    return html


def get_status_badge(status: str) -> str:
    """Return HTML badge for status with color coding."""
    status_lower = status.lower()

    if status_lower == "up":
        return f'<span style="background-color: #06a77d; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✓ {status}</span>'
    elif status_lower == "down":
        return f'<span style="background-color: #e63946; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✗ {status}</span>'
    elif status_lower in ["active", "synced"]:
        return f'<span style="background-color: #06a77d; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">✓ {status}</span>'
    else:
        return f'<span style="background-color: #fcbf49; color: black; padding: 3px 8px; border-radius: 3px; font-weight: bold;">● {status}</span>'


def get_severity_color(severity_str: str) -> tuple:
    """Return color codes for severity level."""
    severity_lower = severity_str.lower()

    if severity_lower == "critical":
        return ("#e63946", "white")  # Vibrant red
    elif severity_lower == "high":
        return ("#f77f00", "white")  # Vibrant orange
    elif severity_lower == "medium":
        return ("#fcbf49", "black")  # Golden yellow
    elif severity_lower == "low":
        return ("#06a77d", "white")  # Fresh teal
    else:
        return ("#8b94a5", "white")  # Soft blue-gray


@st.cache_data
def extract_commands(raw_text: str):
    """Extract and cache command sections from raw text."""
    command_pattern = r'Command:\[\d+\]\s+\[\s*(show\s+[^\]]+)\]'
    commands = re.findall(command_pattern, raw_text, re.IGNORECASE)
    return list(dict.fromkeys(commands))  # Remove duplicates while preserving order


def render_dashboard(analyses: List[tuple[str, ShowTechAnalysis]], best_practices_by_device: Dict = None, raw_text_per_device: Dict[str, str] = None):
    """Render dashboard using native Streamlit components."""

    if best_practices_by_device is None:
        best_practices_by_device = {}
    if raw_text_per_device is None:
        raw_text_per_device = {}

    # Header
    st.title("🔧 Fabric Engine Show Tech Analysis")
    st.markdown(f"**Analyzed {len(analyses)} peer(s)**")
    st.divider()

    # Tabbed interface
    if len(analyses) == 1:
        peer_name, analysis = analyses[0]
        bp_findings = best_practices_by_device.get(peer_name, [])
        render_device_dashboard(peer_name, analysis, bp_findings, raw_text_per_device.get(peer_name, ""))
    else:
        # Add comparison tab for multiple devices
        tab_names = ["📊 Compare"] + [name for name, _ in analyses]
        tabs = st.tabs(tab_names)

        # First tab: Comparison view
        with tabs[0]:
            render_comparison_view(analyses, best_practices_by_device, raw_text_per_device)

        # Device tabs
        for tab, (peer_name, analysis) in zip(tabs[1:], analyses):
            with tab:
                # Show device-specific best practices
                bp_findings = best_practices_by_device.get(peer_name, [])
                render_device_dashboard(peer_name, analysis, bp_findings, raw_text_per_device.get(peer_name, ""))


def render_comparison_view(analyses: List[tuple[str, ShowTechAnalysis]], best_practices_by_device: Dict, raw_text_per_device: Dict[str, str] = None):
    """Render side-by-side comparison of devices."""
    if raw_text_per_device is None:
        raw_text_per_device = {}

    if len(analyses) < 2:
        st.info("Upload multiple Show Tech files to compare devices")
        return

    st.subheader("Side-by-Side Comparison")

    # Create columns for each device
    device_names = [name for name, _ in analyses]
    cols = st.columns(len(analyses))

    # System Information
    st.markdown("### 📋 System Information")
    cols = st.columns(len(analyses))

    for col, (device_name, analysis) in zip(cols, analyses):
        with col:
            st.markdown(f"**{device_name}**")
            st.metric("Model", analysis.system_info.model or "N/A", label_visibility="collapsed")
            st.metric("Version", analysis.system_info.version or "N/A", label_visibility="collapsed")
            st.metric("Uptime", analysis.system_info.uptime or "N/A", label_visibility="collapsed")
            st.metric("Serial", analysis.system_info.serial or "N/A", label_visibility="collapsed")

    # Interface Status
    st.markdown("### 🔗 Interface Status")
    cols = st.columns(len(analyses))

    for col, (device_name, analysis) in zip(cols, analyses):
        with col:
            st.markdown(f"**{device_name}**")
            up_count = len([i for i in analysis.interfaces if i.status and i.status.strip().upper() == "UP"])
            down_count = analysis.down_ports

            # Color code up/down status
            if up_count > 0:
                st.markdown(f"🟢 **Up Ports:** {up_count}")
            else:
                st.markdown(f"⚫ **Up Ports:** {up_count}")

            if down_count > 0:
                st.markdown(f"🔴 **Down Ports:** {down_count}")
            else:
                st.markdown(f"🟢 **Down Ports:** {down_count}")

            st.markdown(f"**Total Ports:** {len(analysis.interfaces)}")

    # VRF/VLAN/ARP Summary
    st.markdown("### 📊 Network Summary")
    cols = st.columns(len(analyses))

    for col, (device_name, analysis) in zip(cols, analyses):
        with col:
            st.markdown(f"**{device_name}**")
            st.metric("VRFs", analysis.vrfs if analysis.vrfs != "N/A" else "N/A")
            st.metric("VLANs", analysis.vlans if analysis.vlans else "N/A")
            st.metric("ARP Entries", analysis.arp_entries if analysis.arp_entries != "N/A" else "N/A")

    # Best Practices Findings
    st.markdown("### ⚠️ Best Practices")
    cols = st.columns(len(analyses))

    for col, (device_name, _) in zip(cols, analyses):
        with col:
            st.markdown(f"**{device_name}**")
            findings = best_practices_by_device.get(device_name, [])

            # Count by severity
            critical = len([f for f in findings if f.severity.value == "critical"])
            high = len([f for f in findings if f.severity.value == "high"])
            medium = len([f for f in findings if f.severity.value == "medium"])
            low = len([f for f in findings if f.severity.value == "low"])

            if critical > 0:
                st.metric("🔴 Critical", critical)
            if high > 0:
                st.metric("🟠 High", high)
            if medium > 0:
                st.metric("🟡 Medium", medium)
            if low > 0:
                st.metric("🔵 Low", low)

            if not findings:
                st.markdown("✅ No issues found")

    # Enabled Features Comparison
    st.markdown("### ✨ Enabled Features")
    cols = st.columns(len(analyses))

    for col, (device_name, analysis) in zip(cols, analyses):
        with col:
            st.markdown(f"**{device_name}**")
            if analysis.system_info.enabled_features:
                features_text = ", ".join(analysis.system_info.enabled_features)
                st.caption(features_text)
            else:
                st.caption("None detected")

    # Show Tech Command Comparison
    st.markdown("### 📝 Show Tech Commands Comparison")

    # Get all available commands from all devices
    all_commands = set()
    for raw_text in raw_text_per_device.values():
        commands = extract_commands(raw_text)
        all_commands.update(commands)

    all_commands = sorted(list(all_commands))

    if all_commands:
        selected_command = st.selectbox(
            "Select a command to compare output:",
            all_commands,
            format_func=lambda x: x[:70] + "..." if len(x) > 70 else x,
            key="compare_cmd_select"
        )

        if selected_command:
            st.markdown(f"**Command:** `{selected_command}`")

            # Extract outputs for all devices
            outputs = {}
            for device_name, _ in analyses:
                raw_text = raw_text_per_device.get(device_name, "")
                if raw_text:
                    section_pattern = rf'(?i){re.escape(selected_command)}.*?(?=Command:\[|\Z)'
                    match = re.search(section_pattern, raw_text, re.DOTALL)
                    if match:
                        outputs[device_name] = match.group(0)

            # Always show side-by-side
            cols = st.columns(len(analyses))

            # For 2 devices, highlight differences
            if len(analyses) == 2 and len(outputs) == 2:
                device_names = [name for name, _ in analyses]
                lines1 = outputs.get(device_names[0], "").split('\n')[:50]
                lines2 = outputs.get(device_names[1], "").split('\n')[:50]

                # Get matcher to find different lines
                matcher = difflib.SequenceMatcher(None, lines1, lines2)
                matching_blocks = matcher.get_matching_blocks()

                # Mark different lines
                diff_lines1 = [False] * len(lines1)
                diff_lines2 = [False] * len(lines2)

                last_i, last_j = 0, 0
                for block in matching_blocks:
                    for idx in range(last_i, block.a):
                        if idx < len(diff_lines1):
                            diff_lines1[idx] = True
                    for idx in range(last_j, block.b):
                        if idx < len(diff_lines2):
                            diff_lines2[idx] = True
                    last_i, last_j = block.a + block.size, block.b + block.size

                # Display side-by-side with highlighting
                for idx, (col, device_name) in enumerate(zip(cols, device_names)):
                    with col:
                        st.markdown(f"**{device_name}**")

                        if idx == 0:
                            lines_to_show = lines1
                            diff_lines = diff_lines1
                            highlight_color = "rgba(230, 57, 70, 0.2)"
                        else:
                            lines_to_show = lines2
                            diff_lines = diff_lines2
                            highlight_color = "rgba(6, 167, 125, 0.2)"

                        # Build HTML with proper line breaks
                        html_parts = []
                        for i, line in enumerate(lines_to_show):
                            if diff_lines[i]:
                                html_parts.append(f'<div style="background-color: {highlight_color}; padding: 2px 4px; margin: 1px 0; font-family: monospace; white-space: pre-wrap; word-break: break-all;">{line}</div>')
                            else:
                                html_parts.append(f'<div style="padding: 2px 4px; margin: 1px 0; font-family: monospace; white-space: pre-wrap; word-break: break-all;">{line}</div>')

                        html = '<div style="background-color: #1a1a1a; padding: 8px; border-radius: 5px; max-height: 500px; overflow-y: auto; color: #d1d5db; font-size: 12px;">'
                        html += '\n'.join(html_parts)
                        html += '</div>'

                        st.markdown(html, unsafe_allow_html=True)
            else:
                # Show side-by-side without highlighting for 1 or 3+ devices
                for col, (device_name, _) in zip(cols, analyses):
                    with col:
                        st.markdown(f"**{device_name}**")

                        if device_name in outputs:
                            output = outputs[device_name]
                            lines = output.split('\n')[:50]
                            st.code('\n'.join(lines), language='text')

                            if len(output.split('\n')) > 50:
                                st.caption(f"... ({len(output.split(chr(10))) - 50} more lines)")
                        else:
                            st.caption("Command output not found")
    else:
        st.info("No commands found in Show Tech files")


def render_device_dashboard(peer_name: str, analysis: ShowTechAnalysis, best_practices_findings: List, raw_text: str):
    """Render dashboard for a single device."""

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Critical Issues", len(analysis.errors), delta=None)
    col2.metric("Warnings", len(analysis.warnings), delta=None)
    col3.metric("Interfaces", len(analysis.interfaces), delta=None)
    col4.metric("Down Ports", analysis.down_ports, delta=None)

    st.divider()

    # System Information
    st.markdown('<a name="system-information"></a>', unsafe_allow_html=True)
    st.header("📋 System Information")
    sys_info = analysis.system_info
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Model:** {sys_info.model}")
        st.write(f"**Version:** {sys_info.version}")
        st.write(f"**Serial:** {sys_info.serial}")
    with col2:
        st.write(f"**Uptime:** {sys_info.uptime}")
        st.write(f"**License:** {sys_info.license}")
        st.write(f"**Base MAC:** {sys_info.base_mac}")

    if sys_info.enabled_features:
        st.write(f"**Enabled Features:** {', '.join(sys_info.enabled_features)}")

    st.divider()

    # Errors
    if analysis.errors:
        st.markdown('<a name="critical-issues"></a>', unsafe_allow_html=True)
        st.header("❌ Critical Issues")
        for error in analysis.errors:
            st.error(f"**{error.message}**" + (f"\n{error.context}" if error.context else ""))
        st.divider()

    # Warnings
    if analysis.warnings:
        st.markdown('<a name="warnings"></a>', unsafe_allow_html=True)
        st.header("⚠️ Warnings")
        for warning in analysis.warnings:
            st.warning(f"**{warning.message}**" + (f"\n{warning.context}" if warning.context else ""))
        st.divider()

    # Best Practices
    if best_practices_findings:
        st.markdown('<a name="best-practices"></a>', unsafe_allow_html=True)
        st.header("✓ Best Practices")
        for finding in best_practices_findings:
            title = getattr(finding, "title", "Finding")
            description = getattr(finding, "description", "")
            severity = getattr(finding, "severity", "")
            recommendation = getattr(finding, "recommendations", "")

            # Extract severity level
            severity_str = str(severity).split('.')[-1].lower() if severity else "low"

            # Display with appropriate alert level
            message = f"**{title}**\n\n{description}"
            if recommendation:
                message += f"\n\n**Recommendation:** {recommendation}"

            if "critical" in severity_str:
                st.error(message)
            elif "medium" in severity_str or "high" in severity_str:
                st.warning(message)
            else:
                st.info(message)
        st.divider()

    # vIST Cluster Health
    if analysis.vist_config.is_vist_member:
        st.markdown('<a name="vist-cluster-health"></a>', unsafe_allow_html=True)
        st.header("🔗 vIST Cluster Health")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Peer IP:** {analysis.vist_config.peer_ip}")
            st.write(f"**Master/Slave Role:** {analysis.vist_config.peer_name}")
        with col2:
            link_status = analysis.vist_config.vist_link_status or "N/A"
            sync_status = analysis.vist_config.sync_status or "N/A"
            st.markdown(f"**vIST Link Status:** {get_status_badge(link_status)}", unsafe_allow_html=True)
            st.markdown(f"**Sync Status:** {get_status_badge(sync_status)}", unsafe_allow_html=True)
        st.divider()

    # Interfaces
    st.markdown('<a name="interfaces"></a>', unsafe_allow_html=True)
    st.header("🔌 Interfaces")
    if analysis.interfaces:
        # Display with color-coded status
        for iface in analysis.interfaces:
            status_badge = get_status_badge(iface.status)
            col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1.5])

            with col1:
                st.markdown(f"**{iface.name}**")
            with col2:
                st.markdown(status_badge, unsafe_allow_html=True)
            with col3:
                st.markdown(f"Speed: {iface.speed or 'N/A'}")
            with col4:
                st.markdown(f"VLAN: {iface.vlan or 'N/A'}")
    else:
        st.info(f"{peer_name}: No interfaces found")

    st.divider()

    # Show Tech Commands sections (lazy load in expander)
    if raw_text:
        st.markdown('<a name="show-tech-commands"></a>', unsafe_allow_html=True)
        with st.expander("📊 Show Tech Commands (Click to Load)", expanded=False):
            render_commands_sections(raw_text, peer_name)


def render_commands_sections(raw_text: str, peer_name: str = ""):
    """Render Show Tech command sections."""
    # Use cached command extraction
    commands = extract_commands(raw_text)

    if not commands:
        return

    # Dropdown to select command (use unique key per device)
    selected_cmd = st.selectbox(
        "Select a command to view:",
        commands,
        format_func=lambda x: x[:60] + "..." if len(x) > 60 else x,
        key=f"cmd_select_{peer_name}"
    )

    if selected_cmd:
        # Find the command output in raw_text
        section_pattern = rf'(?i){re.escape(selected_cmd)}.*?(?=Command:\[|\Z)'
        match = re.search(section_pattern, raw_text, re.DOTALL)
        if match:
            output = match.group(0)
            # Show first 100 lines
            lines = output.split('\n')[:100]
            st.code('\n'.join(lines), language='text')
            if len(output.split('\n')) > 100:
                st.caption(f"(showing first 100 lines of {len(output.split(chr(10)))} total)")
