import subprocess
import uuid
import os
from pathlib import Path


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
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    unique_id = uuid.uuid4().hex
    tex_filename = f"cv_{unique_id}.tex"
    pdf_filename = f"cv_{unique_id}.pdf"
    
    tex_path = output_dir / tex_filename
    pdf_path = output_dir / pdf_filename
    
    try:
        # Write LaTeX content to file
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex)
        
        # Compile LaTeX to PDF (run twice for proper cross-references)
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_filename],
            cwd=str(output_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Run again for cross-references
        if result.returncode == 0:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_filename],
                cwd=str(output_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        # Check if PDF was created
        if pdf_path.exists():
            # Clean up auxiliary files
            aux_files = [
                output_dir / f"cv_{unique_id}.aux",
                output_dir / f"cv_{unique_id}.log",
                output_dir / f"cv_{unique_id}.out",
            ]
            for aux_file in aux_files:
                if aux_file.exists():
                    aux_file.unlink()
            
            return str(pdf_path), True, None
        else:
            error_msg = result.stderr or "PDF was not generated"
            return None, False, error_msg
            
    except Exception as e:
        return None, False, str(e)
    finally:
        # Clean up LaTeX source file (optional - comment out if you want to keep it)
        if tex_path.exists():
            tex_path.unlink()