# LinBlock AI Agent Team

This document indexes the AI agents configured to work on the LinBlock project.

## Team Roster

| ID | Agent | Role | Config File |
|----|-------|------|-------------|
| 001 | Technical Program Manager | Project coordination, planning, risk management | [agent_01_technical_program_manager.md](configs/agent_01_technical_program_manager.md) |
| 002 | Android Platform Architect | AOSP internals, system design, boot sequence | [agent_02_android_platform_architect.md](configs/agent_02_android_platform_architect.md) |
| 003 | Virtualization Engineer | Emulator core, CPU/memory/device emulation | [agent_03_virtualization_engineer.md](configs/agent_03_virtualization_engineer.md) |
| 004 | Linux Systems Engineer | Host optimization, kernel modules, drivers | [agent_04_linux_systems_engineer.md](configs/agent_04_linux_systems_engineer.md) |
| 005 | Security Hardening Specialist | SELinux, permissions, sandboxing, threat modeling | [agent_05_security_hardening_specialist.md](configs/agent_05_security_hardening_specialist.md) |
| 006 | GTK/Python Developer | Emulator GUI, GTK3 widgets, user interface | [agent_06_gtk_python_developer.md](configs/agent_06_gtk_python_developer.md) |
| 007 | Android Build Engineer | AOSP builds, lunch targets, image creation | [agent_07_android_build_engineer.md](configs/agent_07_android_build_engineer.md) |
| 008 | App Management Developer | Permission system, app control, process management | [agent_08_app_management_developer.md](configs/agent_08_app_management_developer.md) |
| 009 | QA/Test Automation Lead | Testing strategy, automation, quality gates | [agent_09_qa_test_automation_lead.md](configs/agent_09_qa_test_automation_lead.md) |
| 010 | DevOps Engineer | CI/CD, build automation, releases | [agent_10_devops_engineer.md](configs/agent_10_devops_engineer.md) |

## Agent Configuration Structure

Each agent config contains:

1. **Identity Block** - Agent ID, name, role
2. **Core Responsibilities** - Primary duties
3. **Capability Block** - Tools and decision authority
4. **Autonomy Block** - Operating mode and boundaries
5. **Coordination Points** - Dependencies on other agents
6. **Initial Tasks** - Activation checklist

## Usage with Claude Code / Claude Max

Load an agent configuration as context when working on related tasks. The agent will operate within its defined boundaries and coordinate with other agents as needed.

Example:
```
# Working on emulator display code
Load: agent_03_virtualization_engineer.md
Load: agent_06_gtk_python_developer.md
```

## Agent Interaction Protocol

1. Agents reference each other by role, not ID
2. Cross-domain decisions require relevant agent consultation
3. Security Specialist reviews all permission-related changes
4. Technical Program Manager coordinates multi-agent work
5. All agents document decisions in /docs

## Folder Structure

```
agents/
├── configs/      # Agent configuration files
├── prompts/      # Reusable prompt templates
├── tools/        # Agent-created tool definitions
└── workflows/    # Multi-agent workflow definitions
```
