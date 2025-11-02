# My CV

A LaTeX-based curriculum vitae template that is ATS-friendly and designed for professional use.

## Features

- Clean, professional design optimized for ATS (Applicant Tracking Systems)
- Uses Times New Roman font (ATS-friendly serif font)
- Minimal color scheme for maximum compatibility
- Well-structured sections for professional experience, education, and certifications
- Responsive layout with proper spacing and formatting

## Prerequisites

You need a LaTeX distribution installed on your system to compile this document.

### Installing LaTeX on macOS

#### Option 1: MacTeX (Full Distribution - Recommended)

MacTeX is the complete TeX Live distribution for macOS. It includes all LaTeX packages and tools.

**Using Homebrew:**
```bash
brew install --cask mactex
```

**Manual Installation:**
1. Download MacTeX from [https://www.tug.org/mactex/](https://www.tug.org/mactex/)
2. Run the installer package
3. After installation, update your PATH:
   ```bash
   eval "$(/usr/libexec/path_helper)"
   ```
   Or restart your terminal.

#### Option 2: BasicTeX (Minimal Distribution)

For a smaller installation (~100MB instead of ~4GB):

```bash
brew install --cask basictex
eval "$(/usr/libexec/path_helper)"
```

You may need to install additional packages:
```bash
sudo tlmgr update --self
sudo tlmgr install enumitem hyperref titlesec fontawesome5 tikz
```

### Installing LaTeX on Linux

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install texlive-full
```

For a minimal installation:
```bash
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended
```

#### Fedora/RHEL/CentOS

```bash
sudo dnf install texlive-scheme-full
```

For a minimal installation:
```bash
sudo dnf install texlive-latex texlive-collection-latexextra texlive-collection-fontsrecommended
```

#### Arch Linux

```bash
sudo pacman -S texlive-most
```

For a minimal installation:
```bash
sudo pacman -S texlive-core texlive-latex texlive-fontsextra
```


## Actual Rendering to PDF

Once LaTeX is installed, compile the document:

```bash
pdflatex -interaction=nonstopmode my_cv.tex
```

For better results (resolving cross-references), run it twice:

```bash
pdflatex -interaction=nonstopmode my_cv.tex
pdflatex my_cv.tex
```

Or in a single command:

```bash
pdflatex my_cv.tex && pdflatex my_cv.tex
```

The output will be `my_cv.pdf` in the same directory.

### Non-interactive Mode

To suppress interactive prompts during compilation:

```bash
pdflatex -interaction=nonstopmode my_cv.tex
```

## Required LaTeX Packages

The CV uses the following packages (usually included in standard LaTeX distributions):

- `geometry` - Page margins and layout
- `enumitem` - Customized list formatting
- `hyperref` - Hyperlinks (configured with hidelinks for ATS compatibility)
- `titlesec` - Section title formatting
- `times` - Times New Roman font
- `fontawesome5` - FontAwesome icons
- `tikz` - Graphics and diagrams
- `array` - Advanced table formatting

## File Structure

```
my_cv/
├── my_cv.tex          # Main LaTeX source file
├── my_cv.pdf          # Compiled PDF (generated)
├── my_cv.aux          # Auxiliary file (generated)
├── my_cv.log          # Compilation log (generated)
├── my_cv.out          # Hyperref output (generated)
└── README.md          # This file
```

## Customization

Edit `my_cv.tex` to update:

- Personal information (name, contact details)
- Professional summary
- Work experience
- Education
- Technical skills
- Certifications

## Notes

- The CV is designed to be ATS-friendly with minimal formatting and standard fonts
- Hyperlinks are hidden using `hidelinks` option for better ATS compatibility
- The document uses A4 paper size with custom margins
- Times New Roman font is used for maximum ATS compatibility

## License

This CV template is for personal use.