from parser import ShowTechAnalysis, Severity
from typing import List, Dict
import re

# Key Show Tech commands to display
FILTERED_COMMANDS = [
    "show alarm database",
    "show core-files",
    "show interfaces gigabitEthernet error",
    "show interfaces gigabitEthernet error collision",
    "show interfaces gigabitEthernet error ospf",
    "show interfaces gigabitEthernet error verbose",
    "show ip vrf",
    "show ip vrrp statistics",
    "show khi performance buffer-pool",
    "show khi performance cpu",
    "show khi performance memory",
    "show logging file",
    "show logging file alarm",
    "show logging file alarm tail",
    "show logging file alarm tail detail",
    "show logging file detail",
    "show logging file tail detail",
    "show logging info",
    "show mit error collision",
    "show mit error main",
    "show pluggable-optical-modules detail",
    "show qos cosq-stats",
    "show qos cosq-stats cpu-port",
    "show qos cosq-stats interface",
    "show running-config",
    "show spanning-tree mstp msti port statistics",
    "show spanning-tree mstp port statistics",
    "show sys-software",
    "show sys-info",
    "show sys-info power",
    "show sys-info temperature",
]

def generate_dashboard(analyses: List[tuple[str, ShowTechAnalysis]], raw_text: str = "", best_practices_findings: List = None) -> str:
    """Generate an interactive HTML dashboard from parsed Show Tech data."""

    if best_practices_findings is None:
        best_practices_findings = []

    html_parts = [
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.1.1/styles/ag-grid.css">',
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.1.1/styles/ag-theme-quartz.css">',
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/choices.js@10.2.0/public/assets/styles/choices.min.css">',
        '<style>',
        STYLES,
        '</style>',
        '<script src="https://cdn.jsdelivr.net/npm/ag-grid-community@31.1.1/dist/ag-grid-community.min.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/choices.js@10.2.0/public/assets/scripts/choices.min.js"></script>',
    ]

    # Header with toggle button
    html_parts.append('<div class="header" id="header">')
    html_parts.append('<label for="nav-show" class="nav-toggle">☰ Sections</label>')
    html_parts.append('<h1>🔧 Fabric Engine Show Tech Analysis</h1>')
    html_parts.append(f'<p>Analyzed {len(analyses)} peer(s)</p>')
    html_parts.append('</div>')

    # Summary metrics
    html_parts.append('<div class="summary">')
    html_parts.append('<h2>Summary</h2>')

    total_errors = sum(len(a[1].errors) for a in analyses)
    total_warnings = sum(len(a[1].warnings) for a in analyses)

    html_parts.append(f'<div class="metric critical">Critical Issues: {total_errors}</div>')
    html_parts.append(f'<div class="metric warning">Warnings: {total_warnings}</div>')

    if analyses:
        first_analysis = analyses[0][1]
        html_parts.append(f'<div class="metric info">Interfaces: {len(first_analysis.interfaces)}</div>')
        html_parts.append(f'<div class="metric info">Down Ports: {first_analysis.down_ports}</div>')

    html_parts.append('</div>')

    # Toggle checkbox and Navigation/TOC - Generate from raw fulltech output
    html_parts.append('<input type="checkbox" id="nav-show" class="nav-show-checkbox">')
    html_parts.append(generate_toc(raw_text))

    # Content sections
    html_parts.append('<div class="content">')

    # System Info
    html_parts.append(generate_system_info_section(analyses))

    # Errors
    html_parts.append(generate_errors_section(analyses))

    # Warnings
    html_parts.append(generate_warnings_section(analyses))

    # Best Practices
    if best_practices_findings:
        html_parts.append(generate_best_practices_section(best_practices_findings))

    # vIST Cluster Health (if vIST members detected)
    vist_members = [(name, analysis) for name, analysis in analyses if analysis.vist_config.is_vist_member]
    if vist_members:
        html_parts.append(generate_vist_cluster_section(vist_members))

    # Interfaces
    html_parts.append(generate_interfaces_section(analyses))

    # All command sections from raw text
    if raw_text:
        html_parts.append(generate_all_sections(raw_text))

    html_parts.append('</div>')

    # Add JavaScript for section navigation and home button
    html_parts.append('<script>')
    html_parts.append('''
function setupNavigation() {
    // Handle all anchor links for smooth scrolling
    var links = document.querySelectorAll('a[href^="#"]');
    links.forEach(function(link) {
        link.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            var targetId = this.getAttribute('href').substring(1);
            var target = document.getElementById(targetId);
            if (target) {
                target.scrollIntoView({behavior: 'smooth'});
            }
            return false;
        };
    });

    // Home button handler - using onclick instead of addEventListener
    var homeBtn = document.querySelector('.home-btn');
    if (homeBtn) {
        homeBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            var header = document.getElementById('header');
            if (header) {
                header.scrollIntoView({behavior: 'smooth'});
            }
            return false;
        };
    }
}

// Setup navigation when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupNavigation);
} else {
    setupNavigation();
}
// Also try after a delay to ensure everything is loaded
setTimeout(setupNavigation, 500);
    ''')
    html_parts.append('</script>')

    return '\n'.join(html_parts)


def generate_toc(raw_text: str) -> str:
    """Generate table of contents from filtered commands only."""
    html = ['<div class="nav">']
    html.append('<h3>📋 Show Tech Sections</h3>')
    html.append('<div class="nav-grid">')

    # Extract all commands from "Command:[N] [ command ]" with their indices
    all_commands = re.finditer(r'Command:\[(\d+)\]\s+\[\s*([^\]]+)\s*\]', raw_text)

    section_count = 0
    for match in all_commands:
        cmd_idx = match.group(1)
        cmd_name = match.group(2).strip()

        # Check if this command matches any filtered command
        if any(filtered in cmd_name for filtered in FILTERED_COMMANDS):
            section_id = f"section-{cmd_idx}"
            label = cmd_name.replace('show ', '').title()
            html.append(f'<a href="#{section_id}" class="nav-link">{label}</a>')
            section_count += 1

    html.append('</div>')
    html.append('</div>')
    return '\n'.join(html)


def generate_all_sections(raw_text: str) -> str:
    """Extract and format filtered command sections from raw text."""
    html = ['<section id="all-sections" class="section">']
    html.append('<h2>📊 Show Tech Commands</h2>')

    # Split by Command:[N]
    sections = re.split(r'Command:\[(\d+)\]\s+\[\s*([^\]]+)\s*\]', raw_text)

    # Process pairs of (index, command, output)
    i = 1
    while i < len(sections) - 1:
        cmd_num = sections[i]
        cmd_name = sections[i+1].strip()
        cmd_output = sections[i+2] if i+2 < len(sections) else ""

        # Only include if command matches filtered list
        if not any(filtered in cmd_name for filtered in FILTERED_COMMANDS):
            i += 3
            continue

        section_id = f"section-{cmd_num}"

        # Clean up command output - remove header line
        output_lines = cmd_output.split('\n')

        # Remove execution time header
        cleaned_output = []
        skip_next = 0
        for line in output_lines:
            if skip_next > 0:
                skip_next -= 1
                continue
            if 'Command Execution Time' in line or '****' in line:
                skip_next = 2
                continue
            cleaned_output.append(line)

        output_text = '\n'.join(cleaned_output).strip()

        if output_text:  # Only add if there's content
            html.append(f'<div id="{section_id}" class="command-section">')
            html.append(f'<div class="section-header"><h3>{cmd_name}</h3><button class="top-btn" onclick="window.scrollTo({{top: 0, behavior: \'smooth\'}})">↑ Top</button></div>')
            html.append('<pre class="command-output">')
            # Escape HTML and preserve formatting
            html.append(escape_html(output_text))
            html.append('</pre>')
            html.append('</div>')

        i += 3

    html.append('</section>')
    return '\n'.join(html)


def escape_html(text: str) -> str:
    """Escape HTML special characters while preserving formatting."""
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))


def generate_system_info_section(analyses: List[tuple[str, ShowTechAnalysis]]) -> str:
    """Generate system information section."""
    html = ['<section id="system" class="section">']
    html.append('<h2>📊 System Information</h2>')

    if not analyses:
        html.append('<p>No data available</p>')
    else:
        for peer_name, analysis in analyses:
            info = analysis.system_info
            html.append('<div class="peer-card">')
            html.append(f'<h3>{peer_name}</h3>')
            html.append('<table class="info-table">')
            html.append(f'<tr><td>Model</td><td>{info.model or "N/A"}</td></tr>')
            html.append(f'<tr><td>Version</td><td>{info.version or "N/A"}</td></tr>')
            html.append(f'<tr><td>Uptime</td><td>{info.uptime or "N/A"}</td></tr>')
            html.append(f'<tr><td>Serial</td><td><code>{info.serial or "N/A"}</code></td></tr>')
            html.append(f'<tr><td>Base MAC</td><td><code>{info.base_mac or "N/A"}</code></td></tr>')
            html.append(f'<tr><td>License</td><td>{info.license or "N/A"}</td></tr>')

            # Enabled features
            if info.enabled_features:
                features_str = ', '.join(info.enabled_features)
                html.append(f'<tr><td>Enabled Features</td><td>{features_str}</td></tr>')
            else:
                html.append(f'<tr><td>Enabled Features</td><td>None detected</td></tr>')

            # Network counts
            html.append(f'<tr><td>Total VRFs</td><td>{analysis.vrfs if analysis.vrfs > 0 else "N/A"}</td></tr>')
            html.append(f'<tr><td>Total VLANs</td><td>{analysis.vlans if analysis.vlans > 0 else "N/A"}</td></tr>')
            html.append(f'<tr><td>Total ARP Entries</td><td>{analysis.arp_entries if analysis.arp_entries > 0 else "N/A"}</td></tr>')

            html.append('</table>')
            html.append('</div>')

    html.append('</section>')
    return '\n'.join(html)


def generate_errors_section(analyses: List[tuple[str, ShowTechAnalysis]]) -> str:
    """Generate errors section."""
    html = ['<section id="errors" class="section">']
    html.append('<h2>❌ Critical Issues</h2>')

    all_errors = []
    for peer_name, analysis in analyses:
        for error in analysis.errors:
            all_errors.append((peer_name, error))

    if not all_errors:
        html.append('<p class="no-issues">✓ No critical issues detected</p>')
    else:
        html.append(f'<p>{len(all_errors)} issue(s) found</p>')
        for peer_name, error in all_errors:
            html.append('<div class="alert critical">')
            html.append(f'<strong>{peer_name}</strong>: {error.message}')
            if error.context:
                html.append(f'<div class="context">{error.context}</div>')
            html.append('</div>')

    html.append('</section>')
    return '\n'.join(html)


def generate_warnings_section(analyses: List[tuple[str, ShowTechAnalysis]]) -> str:
    """Generate warnings section."""
    html = ['<section id="warnings" class="section">']
    html.append('<h2>⚠️ Warnings</h2>')

    all_warnings = []
    for peer_name, analysis in analyses:
        for warning in analysis.warnings:
            all_warnings.append((peer_name, warning))

    if not all_warnings:
        html.append('<p class="no-issues">✓ No warnings detected</p>')
    else:
        html.append(f'<p>{len(all_warnings)} warning(s) found</p>')
        for peer_name, warning in all_warnings:
            html.append('<div class="alert warning">')
            html.append(f'<strong>{peer_name}</strong>: {warning.message}')
            if warning.context:
                html.append(f'<div class="context">{warning.context}</div>')
            html.append('</div>')

    html.append('</section>')
    return '\n'.join(html)


def generate_best_practices_section(best_practices_findings: List) -> str:
    """Generate best practices recommendations section."""
    html = ['<section id="best-practices" class="section">']
    html.append('<h2>📋 Best Practices</h2>')
    html.append('<p style="font-size: 0.9rem; color: #a0a0a0; margin-bottom: 12px;">')
    html.append('Based on <a href="https://extreme-networks.my.site.com/ExtrArticleDetail?an=000131189" target="_blank" style="color: #4080ff;">Extreme Fabric Engine Best Practice Documentation</a>')
    html.append('</p>')

    if not best_practices_findings:
        html.append('<p class="no-issues">✓ All checks passed</p>')
    else:
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(best_practices_findings,
                                key=lambda f: severity_order.get(f.severity.value, 5))

        html.append(f'<p>{len(best_practices_findings)} recommendation(s)</p>')

        for finding in sorted_findings:
            severity_class = finding.severity.value
            html.append(f'<div class="best-practice {severity_class}">')
            html.append(f'<strong>[{finding.severity.value.upper()}]</strong> {finding.category}: {finding.title}')
            html.append(f'<div class="bp-description">{finding.description}</div>')
            html.append(f'<div class="bp-recommendation"><strong>Fix:</strong> {finding.recommendation}</div>')
            html.append('</div>')

    html.append('</section>')
    return '\n'.join(html)


def generate_vist_cluster_section(vist_members: List[tuple[str, ShowTechAnalysis]]) -> str:
    """Generate vIST cluster health section."""
    html = ['<section id="vist-cluster" class="section">']
    html.append('<h2>🔗 vIST Cluster Health</h2>')
    html.append('<button class="top-btn" onclick="window.scrollTo({top: 0, behavior: \'smooth\'})">↑ Top</button>')

    html.append(f'<p>{len(vist_members)} vIST member(s) detected</p>')

    # Create cluster summary table
    html.append('<div class="info-card">')
    html.append('<table class="info-table">')

    for peer_name, analysis in vist_members:
        html.append(f'<tr><td colspan="2" style="font-weight: bold; color: #4080ff;">{peer_name}</td></tr>')

        vist = analysis.vist_config

        # Link status
        link_color = '#44ff88' if vist.vist_link_status == 'up' else '#ff4444'
        link_status = vist.vist_link_status if vist.vist_link_status else 'unknown'
        html.append(f'<tr><td>vIST Link Status</td><td style="color: {link_color};">{link_status}</td></tr>')

        # Peer IP
        if vist.peer_ip:
            html.append(f'<tr><td>Peer IP</td><td><code>{vist.peer_ip}</code></td></tr>')

        # MLT/SMLT Status
        if vist.mlt_status:
            html.append(f'<tr><td>Link Aggregation</td><td>{vist.mlt_status}</td></tr>')

        # Sync Status
        sync_color = '#44ff88' if vist.sync_status == 'synced' else '#ffaa44'
        html.append(f'<tr><td>Synchronization</td><td style="color: {sync_color};">{vist.sync_status}</td></tr>')

        html.append('<tr><td colspan="2"></td></tr>')

    html.append('</table>')
    html.append('</div>')

    # Cluster health assessment
    if len(vist_members) == 2:
        all_links_up = all(v[1].vist_config.vist_link_status == 'up' for v in vist_members)
        all_synced = all(v[1].vist_config.sync_status == 'synced' for v in vist_members)

        if all_links_up and all_synced:
            html.append('<div class="alert" style="background: rgba(68, 255, 136, 0.1); border-left: 4px solid #44ff88;">')
            html.append('<strong>✓ Cluster Health: Optimal</strong><br>')
            html.append('vIST link is up and both peers are synchronized.')
            html.append('</div>')
        else:
            html.append('<div class="alert warning">')
            html.append('<strong>⚠ Cluster Health: Check Required</strong><br>')
            if not all_links_up:
                html.append('One or more vIST links are down. Check vIST link connectivity.<br>')
            if not all_synced:
                html.append('Peers are not synchronized. Check configuration consistency.')
            html.append('</div>')

    html.append('</section>')
    return '\n'.join(html)


def generate_interfaces_section(analyses: List[tuple[str, ShowTechAnalysis]]) -> str:
    """Generate interfaces section with AG-Grid."""
    import json
    html = ['<section id="interfaces" class="section">']
    html.append('<h2>🔌 Interfaces</h2>')

    if not analyses:
        html.append('<p>No data available</p>')
    else:
        for idx, (peer_name, analysis) in enumerate(analyses):
            if not analysis.interfaces:
                html.append(f'<p>{peer_name}: No interfaces found</p>')
                continue

            html.append(f'<h3>{peer_name}</h3>')
            grid_id = f'interfaces-grid-{idx}'
            html.append(f'<div id="{grid_id}" class="ag-theme-quartz" style="height: 400px; width: 100%;"></div>')

            # Prepare data for AG-Grid
            rows = []
            for iface in analysis.interfaces:
                rows.append({
                    'Interface': iface.name,
                    'Status': iface.status,
                    'Speed': iface.speed or 'N/A',
                    'Duplex': iface.duplex or 'N/A',
                    'VLAN': iface.vlan or 'N/A'
                })

            # Add JavaScript to initialize AG-Grid without pagination
            html.append(f'<script>')
            html.append(f'setTimeout(function() {{')
            html.append(f'  const gridDiv = document.getElementById("{grid_id}");')
            html.append(f'  const rowData = {json.dumps(rows)};')
            html.append(f'  const colDefs = [')
            html.append(f'    {{field: "Interface", filter: true, sort: "asc"}},')
            html.append(f'    {{field: "Status", filter: true}},')
            html.append(f'    {{field: "Speed", filter: true}},')
            html.append(f'    {{field: "Duplex", filter: true}},')
            html.append(f'    {{field: "VLAN", filter: true}}')
            html.append(f'  ];')
            html.append(f'  const gridOptions = {{')
            html.append(f'    columnDefs: colDefs,')
            html.append(f'    rowData: rowData,')
            html.append(f'    pagination: false,')
            html.append(f'    suppressPaginationPanel: true')
            html.append(f'  }};')
            html.append(f'  agGrid.createGrid(gridDiv, gridOptions);')
            html.append(f'}}, 500);')
            html.append(f'</script>')
            html.append(f'<style>')
            html.append(f'#{grid_id} {{')
            html.append(f'  height: 600px;')
            html.append(f'  overflow-y: auto;')
            html.append(f'}}')
            html.append(f'</style>')

    html.append('</section>')
    return '\n'.join(html)


STYLES = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #e0e0e0;
    background: #1a1a2e;
}

.header {
    background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
    color: white;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    position: sticky;
    top: 0;
    z-index: 100;
    border-bottom: 2px solid #4080ff;
}

.header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.nav-show-checkbox {
    display: none;
}

.nav-toggle {
    position: absolute;
    top: 2rem;
    right: 2rem;
    background: #4080ff;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    font-size: 0.95rem;
    transition: all 0.3s;
    z-index: 101;
    display: inline-block;
}

.nav-toggle:hover {
    background: #5a9eff;
    transform: scale(1.05);
}

/* Initially hide nav */
.nav {
    display: none;
}

/* Show nav when checkbox is checked */
.nav-show-checkbox:checked ~ .nav {
    display: block;
}

.summary {
    background: #262e4a;
    padding: 2rem;
    margin: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    border: 1px solid #3a4563;
}

.summary h2 {
    grid-column: 1 / -1;
    margin-bottom: 0;
    color: #ffffff;
}

.metric {
    padding: 1rem;
    border-radius: 6px;
    font-weight: 600;
    text-align: center;
}

.metric.critical {
    background: rgba(255, 59, 68, 0.15);
    color: #ff3b44;
    border: 1px solid #ff3b4455;
}

.metric.warning {
    background: rgba(255, 152, 0, 0.15);
    color: #ff9800;
    border: 1px solid #ff980055;
}

.metric.info {
    background: rgba(64, 128, 255, 0.15);
    color: #4080ff;
    border: 1px solid #4080ff55;
}

.nav {
    background: #262e4a;
    padding: 2rem;
    margin: 0 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    position: sticky;
    top: 100px;
    z-index: 50;
    max-height: 80vh;
    overflow-y: auto;
    transition: all 0.3s ease;
    border: 1px solid #3a4563;
}

.nav.collapsed {
    display: none;
}

.nav h3 {
    margin-bottom: 1rem;
    color: #4080ff;
}

.nav-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.5rem;
}

.nav-link {
    display: block;
    padding: 0.5rem;
    background: #3a4563;
    border: 1px solid #4a5a7f;
    border-radius: 4px;
    text-decoration: none;
    color: #4080ff;
    text-align: center;
    font-weight: 600;
    font-size: 0.85rem;
    transition: all 0.3s;
    font-family: inherit;
    cursor: pointer;
}

.nav-link.home-btn {
    grid-column: 1 / -1;
    background: #ff3b44;
    color: white;
    border-color: #ff3b44;
    margin-bottom: 1rem;
}

.nav-link:hover {
    background: #4080ff;
    color: white;
    border-color: #4080ff;
}

.nav-link.home-btn:hover {
    background: #1e8449;
    border-color: #1e8449;
}

.content {
    margin: 2rem;
}

.section {
    background: #262e4a;
    padding: 2rem;
    margin-bottom: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    border: 1px solid #3a4563;
}

.section h2 {
    color: #4080ff;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid #4080ff;
    padding-bottom: 0.5rem;
}

.section h3 {
    color: #5a9eff;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
}

.peer-card {
    background: #1f2843;
    padding: 1.5rem;
    border-radius: 6px;
    margin-bottom: 1rem;
    border-left: 4px solid #4080ff;
    color: #e0e0e0;
}

.info-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}

.info-table td {
    padding: 0.75rem;
    border-bottom: 1px solid #3a4563;
    color: #e0e0e0;
}

.info-table td:first-child {
    font-weight: 600;
    width: 150px;
    color: #4080ff;
}

code {
    background: #1e1e1e;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
    color: #d4d4d4;
}

.alert {
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    border-left: 4px solid;
}

.alert.critical {
    background: rgba(255, 59, 68, 0.15);
    border-color: #ff3b44;
    color: #ff9999;
}

.alert.warning {
    background: rgba(255, 152, 0, 0.15);
    border-color: #ff9800;
    color: #ffb366;
}

.no-issues {
    color: #27ae60;
    font-size: 1.1rem;
    padding: 1rem;
}

.interfaces-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: #e0e0e0;
}

.interfaces-table thead {
    background: #1f2843;
    font-weight: 600;
}

.interfaces-table th {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 2px solid #4080ff;
    color: #4080ff;
}

.interfaces-table td {
    padding: 0.75rem;
    border-bottom: 1px solid #3a4563;
    color: #e0e0e0;
}

.interfaces-table tr.down {
    background: rgba(255, 59, 68, 0.1);
}

.interfaces-table tr.up {
    background: rgba(64, 128, 255, 0.1);
}

.command-section {
    margin: 2rem 0;
    padding: 1.5rem;
    background: #1f2843;
    border-radius: 6px;
    border-left: 4px solid #4080ff;
    scroll-margin-top: 120px;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.command-section h3 {
    color: #5a9eff;
    margin-bottom: 0;
    font-family: 'Monaco', 'Courier New', monospace;
}

.top-btn {
    background: #4080ff;
    color: white;
    border: none;
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    white-space: nowrap;
}

.top-btn:hover {
    background: #5a9eff;
    transform: scale(1.05);
}

.command-output {
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 0.85rem;
    line-height: 1.4;
    font-family: 'Monaco', 'Courier New', monospace;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

::-webkit-scrollbar-track {
    background: #1a1a2e;
}

::-webkit-scrollbar-thumb {
    background: #4080ff;
    border-radius: 6px;
}

::-webkit-scrollbar-thumb:hover {
    background: #5a9eff;
}

/* Firefox scrollbar */
* {
    scrollbar-color: #4080ff #1a1a2e;
    scrollbar-width: thin;
}

@media (max-width: 768px) {
    .header h1 {
        font-size: 1.5rem;
    }

    .nav-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .summary {
        grid-template-columns: 1fr;
    }

    .nav {
        position: static;
        max-height: none;
    }
}

/* AG-Grid Customization */
.ag-theme-quartz {
    --ag-background-color: #262e4a;
    --ag-foreground-color: #ffffff;
    --ag-border-color: #3a4563;
    --ag-grid-size: 6px;
    --ag-font-size: 15px;
    --ag-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #ffffff;
}

.ag-theme-quartz .ag-header {
    background-color: #1f2843;
    font-weight: 700;
    border-bottom: 3px solid #4080ff;
    color: #ffffff;
    font-size: 15px;
}

.ag-theme-quartz .ag-header-cell {
    background-color: #1f2843;
    color: #4080ff;
    padding: 12px 8px;
}

.ag-theme-quartz .ag-row {
    background-color: #262e4a;
    border-bottom: 1px solid #3a4563;
}

.ag-theme-quartz .ag-row:hover {
    background-color: #3a4563;
}

.ag-theme-quartz .ag-row-even {
    background-color: #2a3250;
}

.ag-theme-quartz .ag-cell {
    padding: 12px 8px;
    color: #ffffff;
    display: flex;
    align-items: center;
}

.ag-theme-quartz .ag-cell-value {
    color: #ffffff;
}

.ag-theme-quartz .ag-root-wrapper {
    background-color: #262e4a;
}

.ag-theme-quartz .ag-body-viewport {
    background-color: #262e4a;
}

.ag-theme-quartz .ag-center-cols-container {
    background-color: #262e4a;
}

/* AG-Grid Pagination & Dropdown Styling */
.ag-theme-quartz .ag-paging-panel {
    background-color: #262e4a;
    color: #ffffff;
}

/* Global select styling */
select,
.ag-theme-quartz select,
.ag-theme-quartz .ag-input,
.ag-theme-quartz input[type="text"],
.ag-theme-quartz input[type="number"] {
    background-color: #1f2843 !important;
    color: #ffffff !important;
    border: 1px solid #3a4563 !important;
}

select,
.ag-theme-quartz select {
    appearance: none !important;
    -webkit-appearance: none !important;
    -moz-appearance: none !important;
}

select option,
.ag-theme-quartz select option {
    background-color: #1f2843 !important;
    color: #ffffff !important;
    padding: 8px !important;
}

select option:checked,
.ag-theme-quartz select option:checked {
    background-color: #4080ff !important;
    color: #ffffff !important;
}

.ag-theme-quartz button {
    background-color: #262e4a;
    color: #ffffff;
    border: 1px solid #3a4563;
}

/* Dropdown menu styling */
.ag-theme-quartz .ag-rich-select {
    background-color: #1f2843;
}

.ag-theme-quartz .ag-rich-select-list {
    background-color: #1f2843;
}

.ag-theme-quartz .ag-rich-select-row {
    background-color: #1f2843;
    color: #ffffff;
}

.ag-theme-quartz .ag-rich-select-row:hover {
    background-color: #3a4563;
}

/* Sort and filter icons */
.ag-theme-quartz .ag-sort-indicator-icon {
    color: #4080ff;
}

.ag-theme-quartz .ag-sort-ascending-icon::after,
.ag-theme-quartz .ag-sort-descending-icon::after {
    color: #4080ff;
}

.ag-theme-quartz .ag-filter-icon {
    color: #4080ff;
}

.ag-theme-quartz .ag-column-menu-icon {
    color: #4080ff;
}

/* SVG icons in AG-Grid */
.ag-theme-quartz svg {
    color: #ffffff;
}

.ag-theme-quartz .ag-header-cell-menu-button {
    color: #4080ff;
}

/* Best Practices Section */
.best-practice {
    background: #262e4a;
    border-left: 4px solid #999;
    padding: 12px;
    margin: 8px 0;
    border-radius: 4px;
    color: #ffffff;
}

.best-practice.critical {
    border-left-color: #ff4444;
    background: rgba(255, 68, 68, 0.1);
}

.best-practice.high {
    border-left-color: #ff8844;
    background: rgba(255, 136, 68, 0.1);
}

.best-practice.medium {
    border-left-color: #ffcc44;
    background: rgba(255, 204, 68, 0.1);
}

.best-practice.low {
    border-left-color: #4080ff;
    background: rgba(64, 128, 255, 0.1);
}

.best-practice.info {
    border-left-color: #44ff88;
    background: rgba(68, 255, 136, 0.1);
}

.bp-description {
    margin: 8px 0 4px 0;
    font-size: 0.9rem;
    color: #e0e0e0;
}

.bp-recommendation {
    margin-top: 6px;
    padding: 6px 8px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 3px;
    font-size: 0.85rem;
    color: #d0d0d0;
}
"""
