import re
from utils.logging_config import get_logger

logger = get_logger(__name__)


def extract_text_from_latex(latex_content):
    """
    Extract plain text from LaTeX content by removing LaTeX commands and formatting.
    
    Args:
        latex_content: LaTeX code as string
        
    Returns:
        Plain text extracted from LaTeX
    """
    logger.debug(f"Extracting text from LaTeX, input length: {len(latex_content)}")
    
    # Remove LaTeX commands (e.g., \textbf{}, \section{}, etc.)
    text = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^\}]*\})?', '', latex_content)
    
    # Remove remaining braces
    text = re.sub(r'\{|\}', ' ', text)
    
    # Remove special LaTeX characters
    text = re.sub(r'[\\%$&_#]', ' ', text)
    
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Remove comments
    text = re.sub(r'%.*', '', text)
    
    result = text.strip()
    logger.debug(f"Text extraction complete, output length: {len(result)}")
    return result


def ats_score_keyword_matching(job_desc, cv_latex):
    """
    Calculate ATS score using keyword matching between job description and CV.
    This is a simple keyword-based approach. For better results, use LLM-based scoring.
    
    Args:
        job_desc: Job description text
        cv_latex: CV content in LaTeX format
        
    Returns:
        ATS score from 0-100
    """
    logger.info("Calculating ATS score using keyword matching")
    logger.debug(f"Job description length: {len(job_desc)}, CV LaTeX length: {len(cv_latex)}")
    
    try:
        from sklearn.feature_extraction.text import CountVectorizer
    except ImportError:
        logger.warning("scikit-learn not installed, cannot calculate keyword-based ATS score")
        return 0
    
    # Extract plain text from LaTeX
    cv_text = extract_text_from_latex(cv_latex)
    
    if not cv_text or not job_desc:
        logger.warning("Empty job description or CV text, returning 0")
        return 0
    
    try:
        logger.debug("Creating vectorizer and transforming texts")
        vectorizer = CountVectorizer(stop_words="english")
        vectors = vectorizer.fit_transform([job_desc, cv_text])
        
        jd_vec, cv_vec = vectors.toarray()
        matched = (jd_vec > 0) & (cv_vec > 0)
        
        if jd_vec.sum() == 0:
            logger.warning("No keywords found in job description")
            return 0
        
        score = (matched.sum() / jd_vec.sum()) * 100
        final_score = int(min(100, max(0, score)))
        logger.info(f"Keyword-based ATS score: {final_score}/100 (matched: {matched.sum()}, total: {jd_vec.sum()})")
        return final_score
    except Exception as e:
        logger.error(f"Error in keyword matching ATS score: {str(e)}", exc_info=True)
        return 0