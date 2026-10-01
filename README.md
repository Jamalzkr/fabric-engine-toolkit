# 🧰 Fabric Engine Toolkit

A comprehensive web-based toolkit for Extreme Networks Fabric Engine troubleshooting and VSP switch configuration management.

## 🎯 Features

### 📊 Show Tech Analyzer
Intelligent parsing and analysis of Fabric Engine Show Tech files with:
- **Instant Structured Analysis**: Parse Show Tech files to extract system info, interfaces, errors, warnings, and vIST configuration
- **Multi-Device Support**: Analyze multiple devices at once with per-device session management
- **Best Practices Validation**: 17 official Extreme Networks KB articles integrated for intelligent recommendations
- **vIST Peer Detection**: Automatic detection of vIST cluster pairs and peer health metrics
- **Side-by-Side Comparison**: Compare two devices with command diff highlighting
- **Optional AI Analysis**: Ask Claude for deeper insights on specific issues (requires API key)
- **Color-Coded Status**: Visual indicators for UP/DOWN ports and severity levels

**Supported Information Extraction:**
- System information (model, version, uptime, serial number, license status)
- Interface status and error statistics
- vIST cluster configuration and peer details
- Enabled features (CFM, EAPOL, ISIS, MLT, NTP, RADIUS, SMLT, SPBM, SSHD, SYSLOG, VIST, VRRP, WEB)
- VRF, VLAN, and ARP statistics

### ⚙️ Config Generator
Generate production-ready baseline configurations for VSP switches:
- **10 VSP Models Supported**: VSP4450, VSP4800, VSP4900-24, VSP5520-24, VSP5520-48, VSP5720, VSP7400-48Y, VSP7520, VSP7720, VSP7830
- **VOSS Version Selection**: Support for 8.1/7.1 or older, 8.2.X, 8.3.X-9.0.X, 9.1.X-9.4.X
- **Model-Aware Validation**: Ensures port ranges don't exceed available ports on selected model
- **vIST Cluster Support**: Optional dual-node vIST configuration
- **Port Range Validation**: Supports single and multiple port ranges (e.g., 1/1-1/48 or 1/1-1/24,2/1-2/4)
- **Copy & Download**: One-click copy to clipboard or download as .cfg file
- **Template Management**: Save and load configuration templates for repeated deployments
- **Comprehensive Help**: Built-in documentation with examples and best practices

**Generated Configuration Includes:**
- SSH, SSHD, and SNMP security setup
- ISIS routing and SPBM networking
- VLAN configuration with I/O and NNI ports
- Management IP addressing
- Optional vIST peer configuration with SMLT BMAC
- Complete CLI commands ready for device deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Jamalzkr/fabric-engine-toolkit.git
cd fabric-engine-toolkit

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run app.py
```

The application will open at `http://localhost:8501`

### Optional: Claude AI Integration

To enable AI analysis features in the Show Tech Analyzer:

1. Get an API key from [Anthropic Console](https://console.anthropic.com)
2. Create a `.env` file in the project root:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```
3. The "Ask Claude" section will now appear in the analyzer

## 📖 Usage

### Show Tech Analyzer

1. **Upload Files**
   - Single Show Tech file (.txt, .log, .html)
   - Multiple files
   - ZIP archive containing multiple files

2. **View Analysis**
   - System information summary
   - Interface status with color-coded indicators
   - Error and warning details
   - Best practices recommendations

3. **Compare Devices** (if 2+ files uploaded)
   - Side-by-side system information
   - Interface count and status comparison
   - Command output diff highlighting
   - vIST peer health if applicable

4. **Ask Claude** (optional)
   - Explain critical issues
   - Get fix recommendations for warnings
   - Request configuration review
   - Ask custom questions about the analysis

### Config Generator

1. **Select Tool**: Choose "⚙️ Config Generator" from sidebar

2. **Fill Device Information**
   - Node Name (4 digits, e.g., 4901)
   - Location/Site Name
   - VSP Model (from dropdown)
   - VOSS Version

3. **Enter Network Configuration**
   - Access VLAN ID (for edge connectivity)
   - I/O Ports (connecting to edge switches)
   - NNI Ports (VSP-to-VSP connections)

4. **Optional vIST Setup**
   - Enable vIST cluster mode
   - Select node position (1 or 2)
   - Enter peer node name, vIST VLAN, and base MAC

5. **Generate & Export**
   - Click "Generate Config"
   - Review CLI commands
   - Copy to clipboard or download .cfg file
   - Save as template for future use

## 🔍 Best Practices Validation

The Show Tech Analyzer validates against 17 official Extreme Networks KB articles:

**Security**
- SSHD enablement and configuration
- License status and validity
- Syslog and SNMP configuration
- Password policy compliance

**Configuration**
- Zero Touch Provisioning (ZTP) status
- QoS configuration optimization
- VLAN and VRF best practices

**Redundancy & High Availability**
- vIST cluster health and configuration
- SMLT setup for loop prevention
- Gateway redundancy validation

**Features & Performance**
- Required feature enablement (ISIS, SPBM, CFM)
- Performance tuning recommendations
- Management interface configuration

## 📋 Supported VSP Models

### VSP4000 Series
- VSP4450 (48-port + 2 management)
- VSP4800 (48-port + 2 management)
- VSP4900-24 (24-port Gigabit)

### VSP5000 Series
- VSP5520-24 (24-port Gigabit)
- VSP5520-48 (48-port Gigabit)
- VSP5720 (48-port Gigabit + 8 SFP)

### VSP7000 Series
- VSP7400-48Y (48-port 10G)
- VSP7520 (48-port 10G + 8 SFP)
- VSP7720 (48-port 10G + 8 SFP)
- VSP7830 (48-port 10G + 8 SFP)

## 🔗 References

### Extreme Networks Knowledge Base Articles
The best practices validation uses the following official Extreme Networks KB articles:

- Best Practices for Fabric Engine Configuration
- Security Guidelines for VOSS/Fabric Engine
- vIST Cluster Configuration and Management
- SMLT Setup and Troubleshooting
- ISIS and SPBM Networking
- QoS Configuration Best Practices
- And 11 more comprehensive guides

[View Complete KB Article List](https://extreme-networks.my.site.com/ExtrArticleDetail?an=000131189)

## 🛠️ Technology Stack

- **Frontend Framework**: Streamlit
- **Backend Logic**: Python 3
- **Data Parsing**: Regex-based parsing (no LLM for parsing)
- **Optional AI**: Anthropic Claude API
- **Data Structures**: Python dataclasses

## 📁 Project Structure

```
fabric-engine-tool/
├── app.py                    # Main Streamlit application & router
├── parser.py                 # Show Tech file parsing logic
├── best_practices.py         # Validation against KB articles
├── dashboard_native.py       # Streamlit UI components for analyzer
├── config_gen_logic.py       # Configuration generation logic
├── config_validators.py      # Input validation for config generator
├── config_generator_ui.py    # Config generator Streamlit UI
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore patterns
└── README.md                # This file
```

## 🔐 Security Notes

- Show Tech files are processed locally; no data is sent externally (except to Claude if enabled)
- API keys are stored in `.env` (add to `.gitignore`)
- Port validation prevents invalid configurations
- All inputs are validated before processing

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:
- Additional VSP model support
- More comprehensive best practices checks
- Performance optimizations for large files
- Export formats (JSON, XML, HTML reports)

## 📝 License

MIT License - see LICENSE file for details

## 👤 Author

**Jamal Zakaria** - [@Jamalzkr](https://github.com/Jamalzkr)

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built for Extreme Networks Fabric Engine administrators and engineers** 🚀
