#!/bin/bash
# s016_run_all_create_scripts.sh
# Master script to run all LinBlock file creation scripts
# Ensures files are placed in appropriate locations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/user/projects/linblock"

echo "=============================================="
echo "LinBlock Project File Creation"
echo "=============================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Verify project structure exists
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "ERROR: Project directory does not exist: $PROJECT_ROOT"
    echo "Run s001_linblock_folder_structure.sh first."
    exit 1
fi

# Function to run a script and report status
run_script() {
    local script_name="$1"
    local script_path="$SCRIPT_DIR/$script_name"
    
    if [ -f "$script_path" ]; then
        echo "Running: $script_name"
        chmod +x "$script_path"
        bash "$script_path"
        echo "  Done."
    else
        echo "WARNING: Script not found: $script_path"
    fi
}

echo "Creating project files..."
echo ""

# Run each create script in order
run_script "s002_create_readme.sh"
run_script "s003_create_gitignore.sh"
run_script "s004_create_agents_readme.sh"
run_script "s005_create_agent_01.sh"
run_script "s006_create_agent_02.sh"
run_script "s007_create_agent_03.sh"
run_script "s008_create_agent_04.sh"
run_script "s009_create_agent_05.sh"
run_script "s010_create_agent_06.sh"
run_script "s011_create_agent_07.sh"
run_script "s012_create_agent_08.sh"
run_script "s013_create_agent_09.sh"
run_script "s014_create_agent_10.sh"
run_script "s015_create_architecture_doc.sh"

echo ""
echo "=============================================="
echo "File creation complete."
echo "=============================================="
echo ""
echo "Files created:"
echo ""
find "$PROJECT_ROOT" -type f -name "*.md" | sort
echo ""
find "$PROJECT_ROOT" -type f -name ".gitignore" | sort
echo ""
echo "Next steps:"
echo "1. Review the created files"
echo "2. Initialize git: cd $PROJECT_ROOT && git init"
echo "3. Add files: git add -A"
echo "4. Commit: git commit -m 'Initial project structure'"
echo "5. Push to GitHub: git push -u origin main"
