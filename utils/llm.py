import openai
import google.generativeai as genai


def update_cv_openai(system_prompt, job_description, latex_cv, api_key=None):
    """
    Update CV using OpenAI API.
    
    Args:
        system_prompt: Instructions for what sections to update
        job_description: Job description text
        latex_cv: Original LaTeX CV content
        api_key: OpenAI API key (optional, can be set globally)
        
    Returns:
        Updated LaTeX CV content
    """
    if api_key:
        openai.api_key = api_key
    
    prompt = f"""
    Instructions: {system_prompt}

    Job Description:
    {job_description}

    ORIGINAL LaTeX CV:
    {latex_cv}

    IMPORTANT: return ONLY the full updated LaTeX code.
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def update_cv_gemini(system_prompt, job_description, latex_cv, api_key=None):
    """
    Update CV using Google Gemini API.
    
    Args:
        system_prompt: Instructions for what sections to update
        job_description: Job description text
        latex_cv: Original LaTeX CV content
        api_key: Gemini API key (optional, can be set globally)
        
    Returns:
        Updated LaTeX CV content
    """
    if api_key:
        genai.configure(api_key=api_key)
    
    # Try different model names in order of preference
    # Updated to use available models from the API
    model_names = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest",
        "gemini-pro"
    ]
    
    prompt = f"""
    Instructions: {system_prompt}

    Job Description:
    {job_description}

    ORIGINAL LaTeX CV:
    {latex_cv}

    IMPORTANT: return ONLY the full updated LaTeX code.
    """
    
    last_error = None
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_error = e
            continue
    
    # If all models fail, raise the last error
    raise Exception(f"Failed to generate content with any Gemini model. Last error: {str(last_error)}")


def ats_score_llm(model_choice, job_desc, cv_text, openai_api_key=None, gemini_api_key=None):
    """
    Calculate ATS score using LLM.
    
    Args:
        model_choice: "OpenAI" or "Gemini"
        job_desc: Job description text
        cv_text: CV content (can be LaTeX or plain text)
        openai_api_key: OpenAI API key (optional)
        gemini_api_key: Gemini API key (optional)
        
    Returns:
        ATS score from 0-100
    """
    prompt = f"""
    You are an ATS scoring engine.
    Compare the CV against the job description and output a score from 0–100
    based on keyword matching, relevance, seniority, skills and responsibilities.

    Job Description:
    {job_desc}

    CV:
    {cv_text}

    Output only a number.
    """

    if model_choice == "OpenAI":
        if openai_api_key:
            openai.api_key = openai_api_key
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        try:
            return int(response.choices[0].message.content.strip())
        except ValueError:
            # Try to extract number from response
            import re
            numbers = re.findall(r'\d+', response.choices[0].message.content)
            return int(numbers[0]) if numbers else 0
    else:
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        
        # Try different model names in order of preference
        # Updated to use available models from the API
        model_names = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-1.5-pro-latest",
            "gemini-pro"
        ]
        
        last_error = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                res = model.generate_content(prompt)
                try:
                    return int(res.text.strip())
                except ValueError:
                    # Try to extract number from response
                    import re
                    numbers = re.findall(r'\d+', res.text)
                    return int(numbers[0]) if numbers else 0
            except Exception as e:
                last_error = e
                continue
        
        # If all models fail, return 0
        raise Exception(f"Failed to calculate ATS score with any Gemini model. Last error: {str(last_error)}")