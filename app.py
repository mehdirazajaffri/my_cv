import streamlit as st
import openai
import google.generativeai as genai
from pathlib import Path
from streamlit_pdf_viewer import pdf_viewer

from utils.llm import update_cv_openai, update_cv_gemini, ats_score_llm
from utils.latex import compile_latex
from utils.ats import extract_text_from_latex

# ---------------------
# CONFIGURE API KEYS
# ---------------------
try:
    from streamlit.errors import StreamlitSecretNotFoundError
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    except StreamlitSecretNotFoundError:
        # Handle case where secrets file doesn't exist
        OPENAI_API_KEY = ""
        GEMINI_API_KEY = ""
except (AttributeError, KeyError, Exception):
    # Fallback for other errors
    OPENAI_API_KEY = ""
    GEMINI_API_KEY = ""

if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key-here":
    openai.api_key = OPENAI_API_KEY

if GEMINI_API_KEY and GEMINI_API_KEY != "your-gemini-api-key-here":
    genai.configure(api_key=GEMINI_API_KEY)


# ---------------------
# INITIALIZE SESSION STATE
# ---------------------
if "latex_cv" not in st.session_state:
    # Auto-load CV from file
    cv_file = Path("Mehdi_Raza_Software_Engineer.tex")
    if cv_file.exists():
        with open(cv_file, "r", encoding="utf-8") as f:
            st.session_state["latex_cv"] = f.read()
    else:
        st.session_state["latex_cv"] = ""

if "updated_latex" not in st.session_state:
    st.session_state["updated_latex"] = None

if "pdf_path" not in st.session_state:
    st.session_state["pdf_path"] = None


# ---------------------
# STREAMLIT UI
# ---------------------
st.set_page_config(page_title="Make My CV ATS Friendly", layout="wide")

st.title("Make My CV ATS Friendly")

# System prompt at the top (full width)
system_prompt = st.text_input(
    "System Prompt",
    placeholder="Example: Update the Professional Summary and Technical Skills sections to match the job description...",
    help="Specify which sections of your CV need to be updated"
)

# Model selection
model_choice = st.selectbox(
    "Choose AI Model",
    ["Gemini", "OpenAI"],
    index=0
)

# Two-column layout
left, right = st.columns([1, 1])

with left:
    st.header("Job Description")
    job_desc = st.text_area(
        "Paste Job Description",
        height=400,
        placeholder="Paste the job description here..."
    )
    
    st.header("LaTeX CV Editor")
    latex_cv = st.text_area(
        "Edit Your LaTeX CV",
        value=st.session_state["latex_cv"],
        height=400,
        key="latex_cv_input",
        help="Your LaTeX CV is auto-loaded. You can edit it here."
    )
    
    # Update session state when user edits
    if latex_cv != st.session_state.get("latex_cv_backup", ""):
        st.session_state["latex_cv"] = latex_cv
        st.session_state["latex_cv_backup"] = latex_cv
    
    # Buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Generate CV", type="primary", use_container_width=True):
            if not system_prompt:
                st.warning("Please enter a system prompt to specify which sections to update.")
            elif not job_desc:
                st.warning("Please paste the job description.")
            elif not latex_cv:
                st.warning("Please ensure your LaTeX CV is loaded.")
            else:
                with st.spinner("Generating updated CV..."):
                    try:
                        if model_choice == "Gemini":
                            updated = update_cv_gemini(
                                system_prompt, 
                                job_desc, 
                                latex_cv,
                                GEMINI_API_KEY
                            )
                        else:
                            updated = update_cv_openai(
                                system_prompt, 
                                job_desc, 
                                latex_cv,
                                OPENAI_API_KEY
                            )
                        
                        st.session_state["updated_latex"] = updated
                        st.success("CV generated successfully! Click 'Render PDF' to view.")
                    except Exception as e:
                        st.error(f"Error generating CV: {str(e)}")
    
    with col2:
        if st.button("Calculate ATS Score", use_container_width=True):
            if not job_desc:
                st.warning("Please paste the job description first.")
            else:
                # Use updated CV if available, otherwise use original
                cv_to_score = st.session_state.get("updated_latex") or latex_cv
                
                if not cv_to_score:
                    st.warning("Please generate or load a CV first.")
                else:
                    with st.spinner("Calculating ATS score..."):
                        try:
                            # Extract text from LaTeX for better scoring
                            cv_text = extract_text_from_latex(cv_to_score)
                            score = ats_score_llm(
                                model_choice,
                                job_desc,
                                cv_text,
                                OPENAI_API_KEY,
                                GEMINI_API_KEY
                            )
                            st.session_state["ats_score"] = score
                            st.success(f"ATS Score: **{score} / 100**")
                        except Exception as e:
                            st.error(f"Error calculating ATS score: {str(e)}")


with right:
    st.header("PDF Preview")
    
    # Render PDF button
    if st.button("Render PDF", type="primary", use_container_width=True):
        # Use updated CV if available, otherwise use original
        cv_to_render = st.session_state.get("updated_latex") or latex_cv
        
        if not cv_to_render:
            st.warning("Please generate or load a CV first.")
        else:
            with st.spinner("Compiling LaTeX to PDF..."):
                pdf_path, success, error_msg = compile_latex(cv_to_render)
                
                if success and pdf_path:
                    st.session_state["pdf_path"] = pdf_path
                    st.success("PDF generated successfully!")
                else:
                    st.error(f"Failed to compile PDF: {error_msg or 'Unknown error'}")
                    st.session_state["pdf_path"] = None
    
    # Display PDF if available
    if st.session_state.get("pdf_path"):
        pdf_path = st.session_state["pdf_path"]
        if Path(pdf_path).exists():
            try:
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                    pdf_viewer(pdf_bytes, width=700)
            except Exception as e:
                st.error(f"Error displaying PDF: {str(e)}")
        else:
            st.warning("PDF file not found. Please render again.")
    else:
        st.info("Click 'Render PDF' to compile and view your CV as PDF.")
    
    # Show updated LaTeX code in expander
    if st.session_state.get("updated_latex"):
        with st.expander("View Updated LaTeX Code"):
            st.code(st.session_state["updated_latex"], language="latex")
            
            # Download button for updated LaTeX
            st.download_button(
                label="Download Updated LaTeX",
                data=st.session_state["updated_latex"],
                file_name="updated_cv.tex",
                mime="text/plain"
            )
