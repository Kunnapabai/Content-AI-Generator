## Agentic Prompt Sections

> Ordered list of common and rare agentic prompt sections you can use to build a new prompt.

- `Metadata`
- `# Title`
- `## Purpose`
- `## Variables`
- `## Instructions`
- `## Relevant Files`
- `## Codebase Structure`
- `## Workflow`
- `## Expertise`
- `## Template`
- `## Examples`
- `## Report`

### Metadata

Provides configuration and metadata about the prompt using YAML frontmatter. Includes `allowed-tools` to specify which tools the prompt can use, `description` for prompt identification, `argument-hint` to guide user input, and optionally `model` to set the AI model (sonnet/opus).

### Title

The main heading that names the prompt, typically using a clear, action-oriented name. Should immediately communicate what the prompt does.

### Purpose

Describes what the prompt accomplishes at a high level and its primary use case. Sets context for the user about when and why to use this prompt. Often references key sections like Workflow or Instructions to guide the reader.

### Variables

Defines both dynamic variables (using `$1`, `$2`, `$ARGUMENTS`) that accept user input and static variables with fixed values. You can reference these variables throughout the prompt using `{{variable_name}}` syntax. For higher-order prompts, this is where prompt file paths are specified.

### Instructions

Provides specific guidelines, rules, and constraints for executing the prompt. Written as bullet points detailing important behaviors, edge cases to handle, and critical requirements. Acts as the guardrails ensuring consistent and correct execution.

### Relevant Files

Lists specific files or file patterns that the prompt needs to read, analyze, or modify. Helps establish context and ensures the prompt has access to necessary codebase resources. Particularly useful for prompts that work with existing project structures.

### Codebase Structure

Documents the expected directory layout and file organization relevant to the prompt's operation. Shows where files should be created, where to find existing resources, and how components relate to each other. Essential for prompts that generate or modify project structures.

### Workflow

The core execution steps presented as a numbered list detailing the sequence of operations. Each step should be clear and actionable, often including conditional logic for different scenarios. This is where control flow (loops, conditions) and task delegation to other agents occurs in higher-level prompts.

### Expertise

Contains accumulated knowledge, best practices, and patterns specific to the prompt's domain. Acts as embedded documentation that evolves over time, making the prompt "self-improving" (Level 7). Includes architectural knowledge, discovered patterns, standards, and detailed technical context. This prompt can be self improving but works bets when a separate prompt is dedicated to updating the expertise.

### Template

Provides reusable patterns or boilerplate structures that can be adapted for similar use cases. Often includes code snippets, configuration templates, or structural patterns. Helps users understand how to create variations of the prompt or apply its patterns elsewhere.

### Examples

Demonstrates concrete usage scenarios with actual command invocations and expected outcomes. Shows different parameter combinations and use cases to help users understand the prompt's capabilities. Essential for complex prompts where usage patterns aren't immediately obvious.

### Report

Defines how results should be presented back to the user after execution. Specifies the format, structure, and level of detail for output. Can include markdown templates, required sections, metrics to report, or summary formats that best communicate the work completed.
