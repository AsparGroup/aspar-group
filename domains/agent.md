# ASPAR Agent

## Purpose
Provide a shared intelligence/action layer that preserves context and helps coordinate work across ASPAR domains and client operations.

## Two distinct capability layers
### Internal ASPAR delivery/orchestration
Used by ASPAR to research, design, configure, build and deliver client systems/projects. It may use ChatGPT, Claude Code, MCP, Odoo, Blender, local files, web research and other tools depending on the task.

### Client-facing ASPAR Agent
A bounded interface delivered to a client where useful. It may support tasks such as:
- query sales, customers, stock or team information;
- analyze operational data;
- prepare campaigns or actions;
- retrieve business/project knowledge;
- execute authorized operations with appropriate permissions/approval.

These layers are related but are not equivalent in autonomy, tool access or capability.

## Autonomy ladder
Use progressive autonomy rather than 'agent does everything':
1. Observe
2. Analyze
3. Prepare
4. Execute with approval
5. Automate bounded recurring procedures

High-impact or sensitive actions require explicit permissions, logging and appropriate human approval.

## Shared-memory relationship
ASPAR Agent and other AI workers should read durable context from GitHub Markdown rather than relying on one chat session's memory.

Operational/live business state should be read from the appropriate system (primarily Odoo when relevant), not copied manually into Markdown.

## Architecture principle
Agents are workers over shared context and tools, not independent competing sources of truth.

Avoid free-running agent-to-agent conversations. Prefer structured tasks with explicit owner, expected output, reviewer, stop condition and handoff.

## Current status
Strategic layer is active as a design principle. Client-facing autonomy and full multi-agent orchestration remain incremental capabilities, not a prerequisite for selling current ASPAR services.

## Do not claim
- that client-facing Agent equals the full internal delivery stack;
- unlimited autonomous execution;
- access to tools/data that are not actually connected and authorized;
- reliability beyond what has been tested in the relevant workflow.
