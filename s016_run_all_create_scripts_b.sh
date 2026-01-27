#!/bin/bash
# s016_run_all_create_scripts_b.sh
# Updated master script - uses fixed s018_a
# Run this after s001 folder structure is in place

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

echo "Phase 1: Core project files"
echo "-------------------------------------------"
run_script "s002_create_readme.sh"
run_script "s003_create_gitignore.sh"

echo ""
echo "Phase 2: Agent configurations"
echo "-------------------------------------------"
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

echo ""
echo "Phase 3: Architecture and design documentation"
echo "-------------------------------------------"
run_script "s015_create_architecture_doc.sh"
run_script "s017_create_modular_architecture_doc.sh"
run_script "s018_create_module_template_doc_a.sh"
run_script "s020_create_build_process_doc.sh"

echo ""
echo "Phase 4: Development tools"
echo "-------------------------------------------"
run_script "s019_create_module_generator.sh"

echo ""
echo "=============================================="
echo "File creation complete."
echo "=============================================="
echo ""
echo "Files created:"
echo ""
echo "Documentation:"
find "$PROJECT_ROOT/docs" -type f -name "*.md" 2>/dev/null | sort | sed 's|^|  |'
echo ""
echo "Agent configs:"
find "$PROJECT_ROOT/agents" -type f -name "*.md" 2>/dev/null | sort | sed 's|^|  |'
echo ""
echo "Scripts:"
find "$PROJECT_ROOT/scripts" -type f -name "*.sh" 2>/dev/null | sort | sed 's|^|  |'
echo ""
echo "Root files:"
ls "$PROJECT_ROOT"/*.md "$PROJECT_ROOT"/.gitignore 2>/dev/null | sed 's|^|  |'
echo ""
echo "=============================================="
echo "Next steps:"
echo "1. Review created files"
echo "2. Run: cd $PROJECT_ROOT && git add -A"
echo "3. Run: git commit -m 'Add modular architecture docs'"
echo "4. Create modules: ./scripts/dev/create_module.sh <layer> <name>"
echo "=============================================="
