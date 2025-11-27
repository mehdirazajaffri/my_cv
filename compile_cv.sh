#!/bin/bash

# Script to compile LaTeX CV and clean auxiliary files
# Usage: ./compile_cv.sh [clean]

CV_FILE="Mehdi_Raza_Software_Engineer.tex"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Compiling LaTeX documents...${NC}"

# Compile CV
if [ -f "$CV_FILE" ]; then
    echo -e "${GREEN}Compiling $CV_FILE...${NC}"
    pdflatex -interaction=nonstopmode -halt-on-error "$CV_FILE" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ CV compiled successfully${NC}"
    else
        echo -e "${RED}✗ Error compiling CV${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: $CV_FILE not found${NC}"
    exit 1
fi

# Clean auxiliary files if 'clean' argument is provided
if [ "$1" == "clean" ]; then
    echo -e "${YELLOW}Cleaning auxiliary files...${NC}"
    rm -f *.aux *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz
    echo -e "${GREEN}✓ Auxiliary files cleaned${NC}"
fi

# Define destination directory for CV PDF (update the path as necessary)
DEST_DIR=~/Library/Mobile\ Documents/com\~apple\~CloudDocs/Documents/_CV
DEST_FILE="$DEST_DIR/Mehdi_Raza_Software_Engineer.pdf"

# Ensure destination directory exists
mkdir -p "$DEST_DIR"

# Remove old PDF if it exists
if [ -f "$DEST_FILE" ]; then
    echo -e "${YELLOW}Removing existing CV at $DEST_FILE...${NC}"
    rm -f "$DEST_FILE"
fi

# copy newly compiled PDF to destination
if [ -f "Mehdi_Raza_Software_Engineer.pdf" ]; then
    echo -e "${GREEN}Copying new CV to $DEST_DIR...${NC}"
    cp "Mehdi_Raza_Software_Engineer.pdf" "$DEST_DIR/"
    echo -e "${GREEN}✓ CV PDF copied successfully${NC}"
else
    echo -e "${RED}Error: Compiled PDF not found.${NC}"
    exit 1
fi

echo -e "${GREEN}Done!${NC}"

