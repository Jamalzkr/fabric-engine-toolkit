# Fabric Engine Troubleshooting Tool - Setup Guide

## Prerequisites
- Python 3.9+ installed on your computer
- Your Anthropic API key (from console.anthropic.com)

## Setup Steps

### 1. Create .env file (Secure API Key Storage)
- In the project folder, create a file named `.env` (without the .example)
- Copy the contents from `.env.example`
- Replace `YOUR_API_KEY_HERE` with your actual Anthropic API key
- **Important:** Never commit `.env` to git or share it

Example `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

### 2. Install Dependencies
Open PowerShell in this folder and run:
```
pip install -r requirements.txt
```

### 3. Run the App
In PowerShell, run:
```
streamlit run app.py
```

This will start the web app and open it in your browser (usually http://localhost:8501)

## Using the Tool

1. **Paste Show Tech Output**: Copy the output from a Fabric Engine switch (e.g., `show tech`)
2. **Select Analysis Type**: Choose between Troubleshooting, Configuration Review, or Health Check
3. **Click Analyze**: The tool will analyze the output using Claude AI
4. **Ask Follow-ups**: Chat with the analysis to drill deeper into issues

## Troubleshooting

- **"API key not found" error**: Make sure your `.env` file is in the same folder as `app.py` with the correct API key
- **"ModuleNotFoundError" error**: Run `pip install -r requirements.txt` again
- **Port already in use**: Run `streamlit run app.py --server.port 8502` to use a different port

## Files Explained

- `app.py` - Main application code
- `requirements.txt` - Python dependencies
- `.env` - Your API key (create this, don't share)
- `.env.example` - Template for .env file

## Next Steps

Once this is working:
1. Test with real Show Tech output from Fabric Engine
2. We'll iterate on the analysis to make it smarter
3. Add parsing for specific Fabric Engine sections
4. Phase 2: Config generator
5. Phase 3: Ansible playbooks
