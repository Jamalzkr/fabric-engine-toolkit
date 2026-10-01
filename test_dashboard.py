#!/usr/bin/env python
import sys
sys.path.insert(0, 'C:\\Projects\\fabric-engine-tool')

from parser import parse_show_tech
from dashboard import generate_dashboard
from best_practices import validate_best_practices

# Read the sample Show Tech file
with open('C:\\Projects\\OLRT Switches - Full Tech\\OLRT Switches - Full Tech\\BL-VSP4450-01.log', 'r', encoding='utf-8', errors='replace') as f:
    raw_text = f.read()

# Parse
analysis = parse_show_tech(raw_text)

# Validate best practices
best_practices_findings = validate_best_practices(analysis, raw_text)

# Generate dashboard
analyses = [("BL-VSP4450-01", analysis)]
dashboard_html = generate_dashboard(analyses, raw_text, best_practices_findings)

# Save to file
with open('C:\\Projects\\fabric-engine-tool\\test_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(dashboard_html)

print("Dashboard generated: C:\\Projects\\fabric-engine-tool\\test_dashboard.html")
print(f"System Info: Model={analysis.system_info.model}, Version={analysis.system_info.version}")
print(f"Interfaces: {len(analysis.interfaces)}")
print(f"Errors: {len(analysis.errors)}")
print(f"Warnings: {len(analysis.warnings)}")
