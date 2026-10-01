import streamlit as st
import os
from anthropic import Anthropic
from dotenv import load_dotenv
from parser import parse_show_tech
from dashboard_native import render_dashboard
from best_practices import validate_best_practices
import base64
import zipfile
import io
from pathlib import Path


@st.cache_data
def parse_and_validate(content: str):
    """Cache parsing and best practices validation per device."""
    analysis = parse_show_tech(content)
    findings = validate_best_practices(analysis, content)
    return analysis, findings


@st.cache_resource
def get_dashboard_renderer():
    """Cache the dashboard renderer to avoid re-instantiation."""
    return render_dashboard

load_dotenv()

st.set_page_config(
    page_title="Fabric Engine Toolkit",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize tool selection in session state
if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = "📊 Show Tech Analyzer"

# Add tool selector in sidebar
with st.sidebar:
    st.markdown("# 🧰 Fabric Engine Toolkit")
    st.divider()
    tools = ["📊 Show Tech Analyzer", "⚙️ Config Generator"]
    selected_index = 0 if st.session_state.selected_tool == "📊 Show Tech Analyzer" else 1
    st.session_state.selected_tool = st.radio(
        "Select Tool:",
        tools,
        label_visibility="collapsed",
        index=selected_index
    )
    st.divider()

# Route to appropriate tool
if st.session_state.selected_tool == "⚙️ Config Generator":
    from config_generator_ui import render_config_generator
    render_config_generator()
    st.stop()

# Show Tech Analyzer code continues below
st.title("🔧 Fabric Engine Show Tech Analyzer")
st.markdown("Upload Show Tech files for instant structured analysis and optional AI insights.")

# Initialize API client
api_key = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic() if api_key else None

# Initialize session state
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = {}
if "raw_text_per_device" not in st.session_state:
    st.session_state.raw_text_per_device = {}
if "best_practices_by_device" not in st.session_state:
    st.session_state.best_practices_by_device = {}
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""
if "dashboard_html" not in st.session_state:
    st.session_state.dashboard_html = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "scroll_to_section" not in st.session_state:
    st.session_state.scroll_to_section = None

# Sidebar
with st.sidebar:

    st.header("⚙️ Settings")

    use_ai = st.checkbox(
        "Enable AI Analysis",
        value=True,
        help="Allow asking Claude for deeper insights on specific issues"
    )

    if use_ai and not api_key:
        st.warning("⚠️ API key not configured. AI features disabled.")
        use_ai = False

    st.divider()
    st.markdown("""
    ### How it works:
    1. **Upload Show Tech files** (or paste text)
    2. **Instant analysis** - errors, warnings, metrics highlighted
    3. **Optional AI** - ask Claude to explain issues or suggest fixes
    """)

# File upload
st.subheader("📤 Upload Show Tech Files")

uploaded_files = st.file_uploader(
    "Choose Show Tech files or Zip archive",
    accept_multiple_files=True,
    help="Upload .txt, .log, .html files, or a .zip archive containing multiple Show Tech files"
)

if uploaded_files:
    st.session_state.parsed_data = {}
    st.session_state.raw_text_per_device = {}
    st.session_state.best_practices_by_device = {}

    for file in uploaded_files:
        try:
            # Handle zip files
            if file.name.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(file.read()), 'r') as zip_ref:
                    for zip_file_name in zip_ref.namelist():
                        if not zip_file_name.startswith('__MACOSX') and not zip_file_name.endswith('/'):
                            try:
                                content = zip_ref.read(zip_file_name).decode('utf-8', errors='replace')
                                peer_name = Path(zip_file_name).stem

                                # Parse with progress indicators
                                with st.spinner(f"📊 Parsing {zip_file_name}..."):
                                    analysis, findings = parse_and_validate(content)

                                st.session_state.parsed_data[peer_name] = analysis
                                st.session_state.raw_text_per_device[peer_name] = content
                                st.session_state.best_practices_by_device[peer_name] = findings

                                st.success(f"✅ Parsed {zip_file_name}")
                            except Exception as e:
                                st.error(f"Error parsing {zip_file_name}: {e}")
            else:
                # Handle individual files
                content = file.read().decode('utf-8', errors='replace')
                st.session_state.raw_text = content

                # Parse with progress indicators
                peer_name = file.name.replace('.txt', '').replace('.log', '').replace('.html', '')
                with st.spinner(f"📊 Parsing {file.name}..."):
                    analysis, findings = parse_and_validate(content)

                st.session_state.parsed_data[peer_name] = analysis
                st.session_state.raw_text_per_device[peer_name] = content
                st.session_state.best_practices_by_device[peer_name] = findings

                st.success(f"✅ Parsed {file.name}")
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")

# If data is parsed, generate and display dashboard
if st.session_state.parsed_data:
    st.divider()
    st.subheader("📊 Analysis Dashboard")

    # Use best practices from session state (no recalculation needed)
    analyses_list = list(st.session_state.parsed_data.items())
    render_dashboard(analyses_list, st.session_state.best_practices_by_device, st.session_state.raw_text_per_device)

    # AI Analysis section
    if use_ai:
        st.divider()
        st.subheader("🤖 Ask Claude")
        st.markdown("Ask questions about the analysis or request explanations for specific issues.")

        # Quick action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔍 Explain Critical Issues", key="explain_errors"):
                st.session_state.messages = []

                errors_text = "\n".join([
                    f"- {peer}: {err.message}"
                    for peer, analysis in analyses_list
                    for err in analysis.errors
                ])

                if errors_text:
                    prompt = f"These critical issues were detected in the Show Tech output:\n\n{errors_text}\n\nPlease explain what these issues mean and their potential impact."
                else:
                    prompt = "No critical issues were detected in the Show Tech output."

                st.session_state.messages.append({
                    "role": "user",
                    "content": prompt
                })

        with col2:
            if st.button("⚠️ Fix Warnings", key="fix_warnings"):
                st.session_state.messages = []

                warnings_text = "\n".join([
                    f"- {peer}: {w.message}"
                    for peer, analysis in analyses_list
                    for w in analysis.warnings
                ])

                if warnings_text:
                    prompt = f"These warnings were detected:\n\n{warnings_text}\n\nWhat are the recommended fixes or optimizations?"
                else:
                    prompt = "No warnings were detected."

                st.session_state.messages.append({
                    "role": "user",
                    "content": prompt
                })

        with col3:
            if st.button("📈 Config Review", key="config_review"):
                st.session_state.messages = []

                prompt = "Based on the Show Tech output, what configuration improvements or best practices would you recommend for this Fabric Engine setup?"

                st.session_state.messages.append({
                    "role": "user",
                    "content": prompt
                })

        # Custom questions
        st.markdown("---")
        custom_question = st.text_input(
            "Or ask a custom question:",
            placeholder="e.g., 'Why is interface GigabitEthernet0/1 showing errors?'"
        )

        if custom_question:
            st.session_state.messages.append({
                "role": "user",
                "content": custom_question
            })

        # Process messages
        if st.session_state.messages:
            # Add context to the prompt
            context_text = "Here's the parsed Show Tech data:\n\n"
            for peer, analysis in analyses_list:
                context_text += f"=== {peer} ===\n"
                context_text += f"Model: {analysis.system_info.model}\n"
                context_text += f"Version: {analysis.system_info.version}\n"
                context_text += f"Uptime: {analysis.system_info.uptime}\n"
                context_text += f"Errors: {len(analysis.errors)}\n"
                context_text += f"Warnings: {len(analysis.warnings)}\n"
                context_text += f"Interfaces: {len(analysis.interfaces)}\n\n"

            # Build messages with context
            messages_with_context = [
                {
                    "role": "user",
                    "content": context_text
                }
            ] + st.session_state.messages

            with st.spinner("Analyzing with Claude..."):
                try:
                    response = client.messages.create(
                        model="claude-opus-5",
                        max_tokens=2000,
                        system="You are a Fabric Engine expert. Help users understand their Show Tech output, troubleshoot issues, and optimize their configuration.",
                        messages=messages_with_context
                    )

                    assistant_response = response.content[0].text
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                except Exception as e:
                    st.error(f"Error calling Claude: {e}")

        # Display conversation
        if st.session_state.messages:
            st.markdown("### Conversation")
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        # Only show custom questions, not system context
                        if not msg["content"].startswith("Here's the parsed"):
                            st.markdown(msg["content"])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(msg["content"])

else:
    st.info("👆 Upload Show Tech files to get started")
