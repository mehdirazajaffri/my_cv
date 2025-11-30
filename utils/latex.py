import subprocess
import uuid
import os
from pathlib import Path
from utils.logging_config import get_logger

logger = get_logger(__name__)


def compile_latex(tex):
    """
    Compile LaTeX code to PDF.
    
    Args:
        tex: LaTeX code as string
        
    Returns:
        tuple: (pdf_path, success, error_message)
        - pdf_path: Path to generated PDF if successful, None otherwise
        - success: Boolean indicating if compilation was successful
        - error_message: Error message if compilation failed, None otherwise
    """
    logger.info("Starting LaTeX compilation")
    logger.debug(f"LaTeX content length: {len(tex)} characters")
    
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    logger.debug(f"Output directory: {output_dir}")
    
    # Generate unique filename
    unique_id = uuid.uuid4().hex
    tex_filename = f"cv_{unique_id}.tex"
    pdf_filename = f"cv_{unique_id}.pdf"
    
    tex_path = output_dir / tex_filename
    pdf_path = output_dir / pdf_filename
    
    logger.debug(f"Generated filenames - tex: {tex_filename}, pdf: {pdf_filename}")
    
    try:
        # Write LaTeX content to file
        logger.debug(f"Writing LaTeX to {tex_path}")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex)
        
        # Compile LaTeX to PDF (run twice for proper cross-references)
        logger.debug("Running first pdflatex compilation")
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_filename],
            cwd=str(output_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.debug(f"First compilation return code: {result.returncode}")
        if result.returncode != 0:
            logger.warning(f"First compilation had errors: {result.stderr[:200]}")
        
        # Run again for cross-references
        if result.returncode == 0:
            logger.debug("Running second pdflatex compilation for cross-references")
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_filename],
                cwd=str(output_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        # Check if PDF was created
        if pdf_path.exists():
            pdf_size = pdf_path.stat().st_size
            logger.info(f"PDF compiled successfully: {pdf_path} ({pdf_size} bytes)")
            
            # Clean up auxiliary files
            aux_files = [
                output_dir / f"cv_{unique_id}.aux",
                output_dir / f"cv_{unique_id}.log",
                output_dir / f"cv_{unique_id}.out",
            ]
            cleaned = 0
            for aux_file in aux_files:
                if aux_file.exists():
                    aux_file.unlink()
                    cleaned += 1
            if cleaned > 0:
                logger.debug(f"Cleaned up {cleaned} auxiliary files")
            
            return str(pdf_path), True, None
        else:
            error_msg = result.stderr or "PDF was not generated"
            logger.error(f"PDF compilation failed: {error_msg[:500]}")
            return None, False, error_msg
            
    except Exception as e:
        logger.error(f"Exception during LaTeX compilation: {str(e)}", exc_info=True)
        return None, False, str(e)
    finally:
        # Clean up LaTeX source file (optional - comment out if you want to keep it)
        if tex_path.exists():
            tex_path.unlink()
            logger.debug(f"Cleaned up LaTeX source file: {tex_path}")