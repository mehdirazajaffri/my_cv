import openai
import google.generativeai as genai
import re
from utils.logging_config import get_logger

logger = get_logger(__name__)


def validate_latex_output(latex_output):
    """
    Validate that the generated LaTeX output is complete and not blank.
    
    Args:
        latex_output: Generated LaTeX string
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not latex_output or len(latex_output.strip()) < 100:
        return False, "Generated LaTeX is too short or empty"
    
    # Check for essential LaTeX components
    if "\\documentclass" not in latex_output:
        return False, "Missing \\documentclass"
    
    if "\\begin{document}" not in latex_output:
        return False, "Missing \\begin{document}"
    
    if "\\end{document}" not in latex_output:
        return False, "Missing \\end{document}"
    
    # Check if document is mostly complete (has some content between begin and end)
    doc_start = latex_output.find("\\begin{document}")
    doc_end = latex_output.find("\\end{document}")
    
    if doc_start == -1 or doc_end == -1:
        return False, "Document structure incomplete"
    
    content = latex_output[doc_start + len("\\begin{document}"):doc_end].strip()
    if len(content) < 200:
        return False, f"Document content too short ({len(content)} chars), likely incomplete"
    
    return True, None


def enhance_system_prompt(system_prompt):
    """
    Enhance the system prompt with additional instructions to prevent blank pages.
    
    Args:
        system_prompt: Original system prompt from user
        
    Returns:
        Enhanced system prompt
    """
    enhanced = f"""{system_prompt}

ADDITIONAL REQUIREMENTS:
- Preserve ALL existing content in sections not mentioned above
- Keep the exact same LaTeX formatting and structure
- Do NOT remove any bullet points, items, or content
- Only update/replace keywords and skills in the specified sections
- Maintain the same number of items in lists where possible
- Keep all section headers, dates, and formatting exactly as they are"""
    
    return enhanced


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
    logger.info("Starting OpenAI CV update")
    logger.debug(f"System prompt length: {len(system_prompt)}, Job desc length: {len(job_description)}, CV length: {len(latex_cv)}")
    
    if api_key:
        openai.api_key = api_key
        logger.debug("OpenAI API key set from parameter")
    
    prompt = f"""You are a LaTeX CV editor. Your task is to update ONLY the sections specified in the instructions while preserving ALL other content exactly as it is.

CRITICAL REQUIREMENTS:
1. Return the COMPLETE LaTeX document from \\documentclass to \\end{{document}}
2. Preserve ALL sections that are NOT mentioned in the instructions (Professional Experience, Education, Certifications, etc.) EXACTLY as they appear in the original
3. Only modify the sections explicitly mentioned in the instructions
4. Keep the exact LaTeX structure, formatting, and commands
5. Do NOT remove any content, sections, or items
6. Do NOT change the document structure, packages, or preamble
7. When updating sections, only replace keywords/skills while maintaining the same format and structure

Instructions: {system_prompt}

Job Description:
{job_description}

ORIGINAL LaTeX CV (preserve everything except the sections mentioned in instructions):
{latex_cv}

IMPORTANT: 
- Return the COMPLETE LaTeX document
- Include ALL sections from the original
- Only update the sections specified in the instructions
- Preserve all formatting, commands, and structure
- Do NOT generate a blank or incomplete document"""

    try:
        # Enhance system prompt
        enhanced_system_prompt = enhance_system_prompt(system_prompt)
        prompt = prompt.replace(f"Instructions: {system_prompt}", f"Instructions: {enhanced_system_prompt}")
        
        logger.debug("Sending request to OpenAI API")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content
        
        # Clean up markdown code blocks if present
        if result.startswith("```"):
            result = re.sub(r'^```(?:latex)?\s*\n', '', result, flags=re.MULTILINE)
            result = re.sub(r'\n```\s*$', '', result, flags=re.MULTILINE)
        
        # Validate output
        is_valid, error_msg = validate_latex_output(result)
        if not is_valid:
            logger.error(f"Generated LaTeX validation failed: {error_msg}")
            raise ValueError(f"Generated LaTeX is incomplete: {error_msg}")
        
        logger.info(f"OpenAI CV update completed, response length: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
        raise


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
    
    logger.info("Starting Gemini CV update")
    logger.debug(f"System prompt length: {len(system_prompt)}, Job desc length: {len(job_description)}, CV length: {len(latex_cv)}")
    
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
    
    prompt = f"""You are a LaTeX CV editor. Your task is to update ONLY the sections specified in the instructions while preserving ALL other content exactly as it is.

CRITICAL REQUIREMENTS:
1. Return the COMPLETE LaTeX document from \\documentclass to \\end{{document}}
2. Preserve ALL sections that are NOT mentioned in the instructions (Professional Experience, Education, Certifications, etc.) EXACTLY as they appear in the original
3. Only modify the sections explicitly mentioned in the instructions
4. Keep the exact LaTeX structure, formatting, and commands
5. Do NOT remove any content, sections, or items
6. Do NOT change the document structure, packages, or preamble
7. When updating sections, only replace keywords/skills while maintaining the same format and structure

Instructions: {system_prompt}

Job Description:
{job_description}

ORIGINAL LaTeX CV (preserve everything except the sections mentioned in instructions):
{latex_cv}

IMPORTANT: 
- Return the COMPLETE LaTeX document
- Include ALL sections from the original
- Only update the sections specified in the instructions
- Preserve all formatting, commands, and structure
- Do NOT generate a blank or incomplete document"""
    
    # Enhance system prompt
    enhanced_system_prompt = enhance_system_prompt(system_prompt)
    prompt = prompt.replace(f"Instructions: {system_prompt}", f"Instructions: {enhanced_system_prompt}")
    
    last_error = None
    for model_name in model_names:
        try:
            logger.debug(f"Trying Gemini model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            result = response.text
            
            # Clean up markdown code blocks if present
            if result.startswith("```"):
                result = re.sub(r'^```(?:latex)?\s*\n', '', result, flags=re.MULTILINE)
                result = re.sub(r'\n```\s*$', '', result, flags=re.MULTILINE)
            
            # Validate output
            is_valid, error_msg = validate_latex_output(result)
            if not is_valid:
                logger.warning(f"Model {model_name} generated invalid LaTeX: {error_msg}, trying next model")
                last_error = ValueError(f"Generated LaTeX is incomplete: {error_msg}")
                continue
            
            logger.info(f"Gemini CV update completed with model {model_name}, response length: {len(result)}")
            return result
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {str(e)}")
            last_error = e
            continue
    
    # If all models fail, raise the last error
    logger.error(f"All Gemini models failed. Last error: {str(last_error)}")
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

    logger.info(f"Calculating ATS score using {model_choice}")
    logger.debug(f"Job description length: {len(job_desc)}, CV text length: {len(cv_text)}")
    
    if model_choice == "OpenAI":
        if openai_api_key:
            openai.api_key = openai_api_key
        try:
            logger.debug("Sending ATS score request to OpenAI")
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            raw_score = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI raw response: {raw_score}")
            try:
                score = int(raw_score)
                logger.info(f"OpenAI ATS score: {score}")
                return score
            except ValueError:
                # Try to extract number from response
                import re
                numbers = re.findall(r'\d+', raw_score)
                score = int(numbers[0]) if numbers else 0
                logger.warning(f"Could not parse score directly, extracted: {score}")
                return score
        except Exception as e:
            logger.error(f"OpenAI ATS scoring error: {str(e)}", exc_info=True)
            raise
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
                logger.debug(f"Trying Gemini model for ATS: {model_name}")
                model = genai.GenerativeModel(model_name)
                res = model.generate_content(prompt)
                raw_score = res.text.strip()
                logger.debug(f"Gemini raw response: {raw_score}")
                try:
                    score = int(raw_score)
                    logger.info(f"Gemini ATS score with {model_name}: {score}")
                    return score
                except ValueError:
                    # Try to extract number from response
                    import re
                    numbers = re.findall(r'\d+', raw_score)
                    score = int(numbers[0]) if numbers else 0
                    logger.warning(f"Could not parse score directly, extracted: {score}")
                    return score
            except Exception as e:
                logger.warning(f"Model {model_name} failed for ATS: {str(e)}")
                last_error = e
                continue
        
        # If all models fail, return 0
        logger.error(f"All Gemini models failed for ATS. Last error: {str(last_error)}")
        raise Exception(f"Failed to calculate ATS score with any Gemini model. Last error: {str(last_error)}")