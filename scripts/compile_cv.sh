#!/bin/bash
# Compile a person's LaTeX CV from the repo root.
# Usage: ./scripts/compile_cv.sh [mehdi|ramsha|all] [clean]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PERSON="${1:-mehdi}"
CLEAN="${2:-}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

compile_tex() {
    local dir="$1"
    local tex_file="$2"
    local pdf_name="${tex_file%.tex}.pdf"

    if [ ! -f "$dir/$tex_file" ]; then
        echo -e "${RED}Error: $dir/$tex_file not found${NC}"
        return 1
    fi

    echo -e "${GREEN}Compiling $tex_file...${NC}"
    (
        cd "$dir"
        pdflatex -interaction=nonstopmode -halt-on-error "$tex_file" >/dev/null
        pdflatex -interaction=nonstopmode -halt-on-error "$tex_file" >/dev/null
        if [ "$CLEAN" = "clean" ]; then
            rm -f *.aux *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz
        fi
    )

    if [ -f "$dir/$pdf_name" ]; then
        echo -e "${GREEN}✓ Wrote $dir/$pdf_name${NC}"
    else
        echo -e "${RED}✗ PDF was not created for $tex_file${NC}"
        return 1
    fi
}

copy_mehdi_icloud() {
    local dest_dir="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/_CV"
    local src="$ROOT/people/mehdi/Mehdi_Raza_Software_Engineer.pdf"
    mkdir -p "$dest_dir"
    if [ -f "$src" ]; then
        echo -e "${GREEN}Copying Mehdi CV to iCloud _CV folder...${NC}"
        cp "$src" "$dest_dir/"
    fi
}

echo -e "${YELLOW}Compiling LaTeX documents...${NC}"

case "$PERSON" in
    mehdi)
        compile_tex "$ROOT/people/mehdi" "Mehdi_Raza_Software_Engineer.tex"
        copy_mehdi_icloud
        ;;
    ramsha)
        compile_tex "$ROOT/people/ramsha" "Ramsha_Batool_CV.tex"
        ;;
    all)
        compile_tex "$ROOT/people/mehdi" "Mehdi_Raza_Software_Engineer.tex"
        compile_tex "$ROOT/people/ramsha" "Ramsha_Batool_CV.tex"
        copy_mehdi_icloud
        ;;
    *)
        echo -e "${RED}Unknown person: $PERSON${NC}"
        echo "Usage: ./scripts/compile_cv.sh [mehdi|ramsha|all] [clean]"
        exit 1
        ;;
esac

echo -e "${GREEN}Done!${NC}"
