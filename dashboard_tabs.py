"""Dashboard generation with tab support for multiple devices."""
from typing import List
from parser import ShowTechAnalysis
from dashboard import (
    generate_system_info_section, generate_errors_section,
    generate_warnings_section, generate_best_practices_section,
    generate_vist_cluster_section, generate_all_sections, STYLES
)


def generate_tabbed_dashboard(analyses: List[tuple[str, ShowTechAnalysis]], raw_text: str = "", best_practices_findings: List = None, raw_text_per_device: dict = None) -> str:
    """Generate a tabbed dashboard with one tab per device."""

    if best_practices_findings is None:
        best_practices_findings = []

    if raw_text_per_device is None:
        raw_text_per_device = {}

    html_parts = [
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.1.1/styles/ag-grid.css">',
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.1.1/styles/ag-theme-quartz.css">',
        '<style>',
        STYLES,
        '.tabs { display: flex; gap: 0; border-bottom: 2px solid #4080ff; margin-bottom: 20px; position: sticky; top: 0; z-index: 999; background: #1a1a2e; }',
        '.tab-button { padding: 12px 20px; background: #262e4a; color: #e0e0e0; border: none; cursor: pointer; font-size: 14px; transition: all 0.3s; }',
        '.tab-button.active { background: #4080ff; color: #ffffff; border-bottom: 3px solid #ffffff; }',
        '.tab-button:hover { background: #3a4563; }',
        '.tab-content { display: none; }',
        '.tab-content.active { display: block; }',
        '</style>',
        '<script src="https://cdn.jsdelivr.net/npm/ag-grid-community@31.1.1/dist/ag-grid-community.min.js"></script>',
    ]

    # Header
    html_parts.append('<div class="header" id="header">')
    html_parts.append('<h1>🔧 Fabric Engine Show Tech Analysis</h1>')
    html_parts.append(f'<p>Analyzed {len(analyses)} peer(s)</p>')
    html_parts.append('</div>')

    # Tab buttons
    html_parts.append('<div class="tabs">')
    for idx, (peer_name, _) in enumerate(analyses):
        active_class = 'active' if idx == 0 else ''
        html_parts.append(f'<button class="tab-button {active_class}" onclick="switchTab({idx}, event)">{peer_name}</button>')
    html_parts.append('</div>')

    # Tab content - one per device
    for idx, (peer_name, analysis) in enumerate(analyses):
        active_class = 'active' if idx == 0 else ''
        html_parts.append(f'<div class="tab-content {active_class}" id="tab-{idx}">')

        # Get raw_text for this specific device
        device_raw_text = raw_text_per_device.get(peer_name, raw_text)

        # Generate dashboard content for this device
        html_parts.append(_generate_single_device_dashboard(
            peer_name, analysis, device_raw_text,
            best_practices_findings if idx == 0 else [],
            tab_idx=idx
        ))

        html_parts.append('</div>')

    # Tab switching script
    html_parts.append('<script>')
    html_parts.append('''
function initializeGridsInTab(tabIndex) {
    const tab = document.getElementById('tab-' + tabIndex);
    if (!tab) return;

    const gridDivs = tab.querySelectorAll('[class*="ag-theme-quartz"]');
    gridDivs.forEach(gridDiv => {
        const gridId = gridDiv.id;
        if (!gridId || !window.gridConfigs || !window.gridConfigs[gridId]) return;

        // Skip if already initialized
        if (gridDiv.querySelector('.ag-root')) return;

        const config = window.gridConfigs[gridId];
        const gridOptions = {
            columnDefs: config.columnDefs,
            rowData: config.rowData,
            pagination: false,
            suppressPaginationPanel: true,
            domLayout: "normal"
        };

        agGrid.createGrid(gridDiv, gridOptions);
    });
}

function switchTab(tabIndex, event) {
    event.preventDefault();

    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Deactivate all buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Show selected tab
    const selectedTab = document.getElementById('tab-' + tabIndex);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Activate selected button
    event.target.classList.add('active');

    // Initialize grids in this tab after it becomes visible
    setTimeout(() => initializeGridsInTab(tabIndex), 100);

    // Rebuild sections list for new tab
    setTimeout(() => buildSectionsList(), 100);

    // Setup navigation for new tab
    setupNavigation();
}

function buildSectionsList() {
    // Find all h2 and h3 headings in current tab and build sections list
    var sectionsList = document.getElementById('sections-list');
    if (!sectionsList) return;

    sectionsList.innerHTML = '';

    var activeTab = document.querySelector('.tab-content.active');
    if (!activeTab) return;

    // Find all h2 and h3 headings in the active tab
    var headings = activeTab.querySelectorAll('h2, h3');
    headings.forEach(function(heading, idx) {
        var text = heading.textContent.trim();
        if (!text) return;

        var link = document.createElement('a');
        link.textContent = text;
        link.style.cssText = 'color: #4080ff; text-decoration: none; cursor: pointer; padding: 6px; display: block; word-break: break-word; font-size: 11px;';
        link.onclick = function(e) {
            e.preventDefault();
            heading.scrollIntoView({behavior: 'smooth'});
            return false;
        };

        sectionsList.appendChild(link);
    });
}

function setupNavigation() {
    // Smooth scroll for anchor links
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

    // Build sections list
    buildSectionsList();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setupNavigation();
        setTimeout(() => initializeGridsInTab(0), 100);
    });
} else {
    setupNavigation();
    setTimeout(() => initializeGridsInTab(0), 100);
}
setTimeout(setupNavigation, 500);
    ''')
    html_parts.append('</script>')

    return '\n'.join(html_parts)


def _generate_single_device_dashboard(peer_name: str, analysis: ShowTechAnalysis, raw_text: str, best_practices_findings: List, tab_idx: int = 0) -> str:
    """Generate dashboard content for a single device."""
    import json
    html = []

    # Summary
    html.append('<div class="summary">')
    html.append(f'<h2>{peer_name}</h2>')
    html.append(f'<div class="metric critical">Critical Issues: {len(analysis.errors)}</div>')
    html.append(f'<div class="metric warning">Warnings: {len(analysis.warnings)}</div>')
    html.append(f'<div class="metric info">Interfaces: {len(analysis.interfaces)}</div>')
    html.append(f'<div class="metric info">Down Ports: {analysis.down_ports}</div>')
    html.append('</div>')

    # System Info
    html.append(generate_system_info_section([(peer_name, analysis)]))

    # Errors
    html.append(generate_errors_section([(peer_name, analysis)]))

    # Warnings
    html.append(generate_warnings_section([(peer_name, analysis)]))

    # Best Practices (only on first tab)
    if best_practices_findings:
        html.append(generate_best_practices_section(best_practices_findings))

    # vIST Cluster Health
    if analysis.vist_config.is_vist_member:
        html.append(generate_vist_cluster_section([(peer_name, analysis)]))

    # Interfaces
    html.append(f'<section id="interfaces" class="section">')
    html.append('<h2>🔌 Interfaces</h2>')

    if not analysis.interfaces:
        html.append(f'<p>{peer_name}: No interfaces found</p>')
    else:
        grid_id = f'grid-{tab_idx}'
        html.append(f'<div id="{grid_id}" class="ag-theme-quartz" style="height: 600px; width: 100%;"></div>')

        # Prepare rows
        rows = []
        for iface in analysis.interfaces:
            rows.append({
                'Interface': iface.name,
                'Status': iface.status,
                'Speed': iface.speed or 'N/A',
                'Duplex': iface.duplex or 'N/A',
                'VLAN': iface.vlan or 'N/A'
            })

        # Store grid config for deferred initialization on tab switch
        html.append('<script type="text/javascript">')
        html.append(f'window.gridConfigs = window.gridConfigs || {{}};')
        html.append(f'window.gridConfigs["{grid_id}"] = {{')
        html.append(f'  columnDefs: [')
        html.append(f'    {{field: "Interface", filter: true, sort: "asc"}},')
        html.append(f'    {{field: "Status", filter: true}},')
        html.append(f'    {{field: "Speed", filter: true}},')
        html.append(f'    {{field: "Duplex", filter: true}},')
        html.append(f'    {{field: "VLAN", filter: true}}')
        html.append(f'  ],')
        html.append(f'  rowData: {json.dumps(rows)}')
        html.append(f'}};')
        html.append('</script>')

    html.append('</section>')

    # Command sections
    if raw_text:
        html.append(generate_all_sections(raw_text))

    return '\n'.join(html)
