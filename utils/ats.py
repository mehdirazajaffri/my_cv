import re


def extract_text_from_latex(latex_content):
    """
    Extract plain text from LaTeX content by removing LaTeX commands and formatting.
    
    Args:
        latex_content: LaTeX code as string
        
    Returns:
        Plain text extracted from LaTeX
    """
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
    
    return text.strip()


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
    try:
        from sklearn.feature_extraction.text import CountVectorizer
    except ImportError:
        # sklearn not installed, return 0
        return 0
    
    # Extract plain text from LaTeX
    cv_text = extract_text_from_latex(cv_latex)
    
    if not cv_text or not job_desc:
        return 0
    
    try:
        vectorizer = CountVectorizer(stop_words="english")
        vectors = vectorizer.fit_transform([job_desc, cv_text])
        
        jd_vec, cv_vec = vectors.toarray()
        matched = (jd_vec > 0) & (cv_vec > 0)
        
        if jd_vec.sum() == 0:
            return 0
        
        score = (matched.sum() / jd_vec.sum()) * 100
        return int(min(100, max(0, score)))
    except Exception:
        return 0