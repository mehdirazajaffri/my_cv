# CV workspace

LaTeX CVs and cover letters, plus a Streamlit app that rewrites a CV against a job description and scores ATS match.

Documents live under `people/`, one folder per person. The app and compile script stay at the repo root.

## Layout

```
my_cv/
├── app.py                          # Streamlit ATS optimizer
├── requirements.txt
├── people/
│   ├── mehdi/
│   │   ├── Mehdi_Raza_Software_Engineer.tex
│   │   ├── Mehdi_Raza_Software_Engineer.pdf
│   │   ├── cover_letter.tex
│   │   └── cover_letter.pdf
│   └── ramsha/
│       ├── Ramsha_Batool_CV.tex    # ATS-oriented LaTeX CV
│       ├── Ramsha_Batool_CV.pdf
│       ├── Ramsha_Batool_CV.yaml   # RenderCV source (optional)
│       ├── Ramsha_Batool_Cover_Letter.tex
│       └── Ramsha_Batool_Cover_Letter.pdf
├── scripts/
│   └── compile_cv.sh               # pdflatex helper
└── utils/                          # LLM, LaTeX compile, ATS helpers
```

Generated files (`output/`, `logs/`, `rendercv_output/`, `*.aux`, `*.log`) are gitignored.

## Compile a CV

Needs a LaTeX distribution (`pdflatex` on your PATH). From the repo root:

```bash
./scripts/compile_cv.sh mehdi
./scripts/compile_cv.sh ramsha
./scripts/compile_cv.sh all
./scripts/compile_cv.sh ramsha clean   # also remove aux files
```

`./compile_cv.sh` at the repo root is a shortcut to the same script.

Or compile a file directly:

```bash
cd people/ramsha
pdflatex -interaction=nonstopmode Ramsha_Batool_CV.tex
pdflatex -interaction=nonstopmode Ramsha_Batool_CV.tex
```

The Mehdi compile also copies the PDF to iCloud `Documents/_CV` when that folder exists.

### Optional: RenderCV (Ramsha YAML)

```bash
uv tool install "rendercv[full]"
rendercv render people/ramsha/Ramsha_Batool_CV.yaml
```

## Streamlit ATS app

Rewrites Mehdi’s LaTeX CV against a pasted job description and can score the match.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Put API keys in `.streamlit/secrets.toml` (not committed):

```toml
OPENAI_API_KEY = "..."
GEMINI_API_KEY = "..."
```

The sidebar reloads `people/mehdi/Mehdi_Raza_Software_Engineer.tex`. Generated PDFs go to `output/`.

## Install LaTeX

**macOS (recommended):** `brew install --cask mactex`, then restart the terminal.

**macOS (smaller):** `brew install --cask basictex`, then:

```bash
sudo tlmgr update --self
sudo tlmgr install enumitem hyperref titlesec
```

**Ubuntu/Debian:** `sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended`

**Fedora:** `sudo dnf install texlive-latex texlive-collection-latexextra texlive-collection-fontsrecommended`

Packages used: `geometry`, `enumitem`, `hyperref`, `titlesec`, `times`. Mehdi’s CV also uses `fontawesome5`.

## Editing

- **Mehdi:** edit `people/mehdi/Mehdi_Raza_Software_Engineer.tex`
- **Ramsha:** edit `people/ramsha/Ramsha_Batool_CV.tex` (this is the ATS-safe version used for applications)

Keep CVs as text PDFs (Times, standard headings, single column, no icon fonts in Ramsha’s file) so applicant tracking systems can parse name, contact, jobs, and dates.

## License

Personal use.
