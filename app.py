import streamlit as st
import openai
import google.generativeai as genai
import logging
from pathlib import Path
from streamlit_pdf_viewer import pdf_viewer

from utils.llm import update_cv_openai, update_cv_gemini, ats_score_llm
from utils.latex import compile_latex
from utils.ats import extract_text_from_latex
from utils.logging_config import setup_logging, get_logger

# Set up logging
logger = get_logger(__name__)
setup_logging(log_level=logging.INFO)

# ---------------------
# CONFIGURE API KEYS
# ---------------------
try:
    from streamlit.errors import StreamlitSecretNotFoundError
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
        logger.info("API keys loaded from secrets file")
    except StreamlitSecretNotFoundError:
        # Handle case where secrets file doesn't exist
        OPENAI_API_KEY = ""
        GEMINI_API_KEY = ""
        logger.warning("Secrets file not found, API keys not loaded")
except (AttributeError, KeyError, Exception) as e:
    # Fallback for other errors
    OPENAI_API_KEY = ""
    GEMINI_API_KEY = ""
    logger.error(f"Error loading secrets: {str(e)}")

if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key-here":
    openai.api_key = OPENAI_API_KEY
    logger.info("OpenAI API key configured")
else:
    logger.warning("OpenAI API key not configured")

if GEMINI_API_KEY and GEMINI_API_KEY != "your-gemini-api-key-here":
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API key configured")
else:
    logger.warning("Gemini API key not configured")


# ---------------------
# INITIALIZE SESSION STATE
# ---------------------
if "latex_cv" not in st.session_state:
    # Auto-load CV from file
    cv_file = Path("Mehdi_Raza_Software_Engineer.tex")
    if cv_file.exists():
        with open(cv_file, "r", encoding="utf-8") as f:
            st.session_state["latex_cv"] = f.read()
        logger.info(f"CV loaded from {cv_file}, size: {len(st.session_state['latex_cv'])} characters")
    else:
        st.session_state["latex_cv"] = ""
        logger.warning(f"CV file not found: {cv_file}")

if "updated_latex" not in st.session_state:
    st.session_state["updated_latex"] = None

if "pdf_path" not in st.session_state:
    st.session_state["pdf_path"] = None


# ---------------------
# STREAMLIT UI
# ---------------------
st.set_page_config(
    page_title="Make My CV ATS Friendly",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "CV ATS Optimizer - Make your CV ATS-friendly with AI"
    }
)

# ===== SIDEBAR =====
with st.sidebar:
    st.title("Settings")
    
    # Model selection
    model_choice = st.radio(
        "🤖 AI Model",
        ["Gemini", "OpenAI"],
        index=0,
        help="Choose the AI model for CV generation"
    )
    
    st.divider()
    
    # Status indicators
    st.subheader("📊 Status")
    col1, col2 = st.columns(2)
    with col1:
        if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key-here":
            st.success("✅ OpenAI")
        else:
            st.error("❌ OpenAI")
    with col2:
        if GEMINI_API_KEY and GEMINI_API_KEY != "your-gemini-api-key-here":
            st.success("✅ Gemini")
        else:
            st.error("❌ Gemini")
    
    if st.session_state.get("latex_cv"):
        cv_size = len(st.session_state["latex_cv"])
        st.success(f"📄 CV Loaded ({cv_size:,} chars)")
    else:
        st.warning("⚠️ CV Not Loaded")
    
    st.divider()
    
    # Quick actions
    st.subheader("🔧 Quick Actions")
    if st.button("🔄 Reload CV File", use_container_width=True):
        cv_file = Path("Mehdi_Raza_Software_Engineer.tex")
        if cv_file.exists():
            with open(cv_file, "r", encoding="utf-8") as f:
                st.session_state["latex_cv"] = f.read()
            st.session_state["latex_cv_backup"] = st.session_state["latex_cv"]
            st.success("CV reloaded!")
            logger.info("CV reloaded from file")
            st.rerun()
        else:
            st.error("CV file not found!")
    
    if st.button("📥 Download Latest PDF", use_container_width=True, disabled=not st.session_state.get("pdf_path")):
        if st.session_state.get("pdf_path") and Path(st.session_state["pdf_path"]).exists():
            with open(st.session_state["pdf_path"], "rb") as pdf_file:
                st.download_button(
                    label="💾 Download PDF",
                    data=pdf_file.read(),
                    file_name="cv.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    st.divider()
    
    # Info
    st.info("💡 **Tip**: Be specific in your instructions for best results!")

# ===== MAIN CONTENT =====
# Header with title and ATS score
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title("Make my CV ATS friendly bro")
    st.caption("Optimize your CV for Applicant Tracking Systems using AI")
with header_col2:
    if st.session_state.get("ats_score") is not None:
        score = st.session_state["ats_score"]
        delta = score - 50
        st.metric(
            "ATS Score",
            f"{score}/100",
            delta=f"{delta:+d}",
            delta_color="normal" if score >= 50 else "inverse",
            help="Your CV's match score with the job description"
        )
    else:
        st.metric("ATS Score", "—", help="Calculate ATS score to see your match")

st.divider()

# Main workflow in two columns
left_col, right_col = st.columns([1, 1])

with left_col:
    # Input section
    st.subheader("📝 Input")
    
    # Job description in expandable container
    with st.expander("📋 Job Description", expanded=True):
        job_desc = st.text_area(
            "Paste the job description here",
            height=250,
            placeholder="Copy and paste the complete job description...",
            label_visibility="collapsed",
            help="The more detailed the job description, the better the results"
        )
        if job_desc:
            st.caption(f"📊 {len(job_desc.split())} words, {len(job_desc)} characters")
    
    # Instructions
    with st.expander("✏️ Customization Instructions", expanded=True):
        system_prompt = st.text_area(
            "What should be updated?",
            height=120,
            placeholder="Example: Update Professional Summary and Technical Skills sections to match job description keywords. Only replace existing keywords, don't change structure.",
            label_visibility="collapsed",
            help="Be specific about which sections to update"
        )
        if system_prompt:
            st.caption(f"📝 {len(system_prompt)} characters")
    
    # CV Editor (collapsed by default)
    with st.expander("📄 LaTeX CV Editor (Advanced)", expanded=False):
        latex_cv_editor = st.text_area(
            "Edit your LaTeX CV",
            value=st.session_state.get("latex_cv", ""),
            height=300,
            key="latex_cv_input",
            help="Your CV is auto-loaded. Edit here if needed."
        )
        if latex_cv_editor != st.session_state.get("latex_cv_backup", ""):
            st.session_state["latex_cv"] = latex_cv_editor
            st.session_state["latex_cv_backup"] = latex_cv_editor
    
    # Always use session state for latex_cv
    latex_cv = st.session_state.get("latex_cv", "")
    
    # Action buttons
    st.divider()
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("🚀 Generate CV", type="primary", use_container_width=True, help="Generate updated CV based on job description"):
            if not system_prompt:
                logger.warning("Generate CV clicked but system prompt is empty")
                st.warning("Please enter a system prompt to specify which sections to update.")
            elif not job_desc:
                logger.warning("Generate CV clicked but job description is empty")
                st.warning("Please paste the job description.")
            elif not latex_cv:
                logger.warning("Generate CV clicked but LaTeX CV is empty")
                st.warning("Please ensure your LaTeX CV is loaded.")
            else:
                logger.info(f"Starting CV generation with model: {model_choice}, prompt length: {len(system_prompt)}, job desc length: {len(job_desc)}")
                with st.spinner("Generating updated CV..."):
                    try:
                        if model_choice == "Gemini":
                            logger.debug("Using Gemini model for CV generation")
                            updated = update_cv_gemini(
                                system_prompt, 
                                job_desc, 
                                latex_cv,
                                GEMINI_API_KEY
                            )
                        else:
                            logger.debug("Using OpenAI model for CV generation")
                            updated = update_cv_openai(
                                system_prompt, 
                                job_desc, 
                                latex_cv,
                                OPENAI_API_KEY
                            )
                        
                        st.session_state["updated_latex"] = updated
                        logger.info(f"CV generated successfully, output length: {len(updated)} characters")
                        st.success("CV generated successfully! Click 'Render PDF' to view.")
                    except Exception as e:
                        logger.error(f"Error generating CV: {str(e)}", exc_info=True)
                        st.error(f"Error generating CV: {str(e)}")
    
    with action_col2:
        if st.button("📊 Calculate ATS Score", use_container_width=True, help="Calculate how well your CV matches the job description"):
            if not job_desc:
                logger.warning("Calculate ATS Score clicked but job description is empty")
                st.warning("Please paste the job description first.")
            else:
                # Use updated CV if available, otherwise use original
                cv_to_score = st.session_state.get("updated_latex") or latex_cv
                
                if not cv_to_score:
                    logger.warning("Calculate ATS Score clicked but no CV available")
                    st.warning("Please generate or load a CV first.")
                else:
                    logger.info(f"Calculating ATS score with model: {model_choice}, CV length: {len(cv_to_score)}")
                    with st.spinner("Calculating ATS score..."):
                        try:
                            # Extract text from LaTeX for better scoring
                            cv_text = extract_text_from_latex(cv_to_score)
                            logger.debug(f"Extracted text length: {len(cv_text)}")
                            score = ats_score_llm(
                                model_choice,
                                job_desc,
                                cv_text,
                                OPENAI_API_KEY,
                                GEMINI_API_KEY
                            )
                            st.session_state["ats_score"] = score
                            logger.info(f"ATS score calculated: {score}/100")
                            st.success(f"ATS Score: **{score} / 100**")
                            # Rerun to update header metric
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Error calculating ATS score: {str(e)}", exc_info=True)
                            st.error(f"Error calculating ATS score: {str(e)}")


with right_col:
    # Output section
    st.subheader("📄 Output")
    
    # PDF Preview section
    pdf_container = st.container()
    with pdf_container:
        if st.session_state.get("pdf_path") and Path(st.session_state["pdf_path"]).exists():
            st.success("✅ PDF Ready")
            if st.button("🔄 Re-render PDF", use_container_width=True, key="rerender_pdf"):
                cv_to_render = st.session_state.get("updated_latex") or latex_cv
                if cv_to_render:
                    logger.info(f"Re-rendering PDF, CV length: {len(cv_to_render)} characters")
                    with st.spinner("Compiling LaTeX to PDF..."):
                        pdf_path, success, error_msg = compile_latex(cv_to_render)
                        if success and pdf_path:
                            st.session_state["pdf_path"] = pdf_path
                            logger.info(f"PDF re-rendered successfully: {pdf_path}")
                            st.success("PDF re-rendered successfully!")
                            st.rerun()
                        else:
                            logger.error(f"PDF re-rendering failed: {error_msg or 'Unknown error'}")
                            st.error(f"Failed to re-render PDF: {error_msg or 'Unknown error'}")
        else:
            st.info("⏳ Click 'Render PDF' to generate preview")
        
        if st.button("📄 Render PDF", type="primary", use_container_width=True):
            # Use updated CV if available, otherwise use original
            cv_to_render = st.session_state.get("updated_latex") or latex_cv
            
            if not cv_to_render:
                logger.warning("Render PDF clicked but no CV available")
                st.warning("Please generate or load a CV first.")
            else:
                logger.info(f"Starting PDF compilation, CV length: {len(cv_to_render)} characters")
                with st.spinner("Compiling LaTeX to PDF..."):
                    pdf_path, success, error_msg = compile_latex(cv_to_render)
                    
                    if success and pdf_path:
                        st.session_state["pdf_path"] = pdf_path
                        logger.info(f"PDF compiled successfully: {pdf_path}")
                        st.success("PDF generated successfully!")
                        st.rerun()
                    else:
                        logger.error(f"PDF compilation failed: {error_msg or 'Unknown error'}")
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
    
    st.divider()
    
    # Updated LaTeX code
    if st.session_state.get("updated_latex"):
        with st.expander("📝 View Updated LaTeX Code", expanded=False):
            st.code(st.session_state["updated_latex"], language="latex")
            
            st.download_button(
                label="💾 Download Updated LaTeX",
                data=st.session_state["updated_latex"],
                file_name="updated_cv.tex",
                mime="text/plain",
                use_container_width=True
            )
    
    # ATS Score display
    if st.session_state.get("ats_score"):
        st.divider()
        score = st.session_state["ats_score"]
        
        # Visual score indicator
        st.subheader("📊 ATS Analysis")
        
        # Progress bar
        st.progress(score / 100)
        st.caption(f"Match Score: {score}/100")
        
        # Score interpretation
        if score >= 80:
            st.success("🎉 Excellent match! Your CV aligns well with the job description.")
        elif score >= 60:
            st.info("👍 Good match. Consider adding more relevant keywords.")
        elif score >= 40:
            st.warning("⚠️ Moderate match. Review and update more sections.")
        else:
            st.error("❌ Low match. Significant updates needed.")

# Footer
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption("💡 **Tip**: Use specific instructions for best results")
with footer_col2:
    st.caption("📚 Check logs for detailed information")
with footer_col3:
    st.caption(f"🤖 Using: {model_choice}")
