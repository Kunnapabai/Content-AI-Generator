---
allowed-tools: Read, Write, Glob, Grep, AskUserQuestion, TodoWrite
description: Iteratively build a detailed specification through one-question-at-a-time discovery
argument-hint: [idea-or-feature-description] [path/to/related/file]
model: opus
---

# Purpose

This prompt guides an iterative specification-building process. It asks one question at a time, with each question building on previous answers, to develop a thorough, developer-ready specification. The prompt follows the `Instructions` to deeply understand the user's idea and outputs a comprehensive spec to `requirements/`.

## Variables

IDEA_INPUT: $1
CONTEXT_FILE_PATH: $2
OUTPUT_DIRECTORY: requirements

## Instructions

- Begin by reading the `CONTEXT_FILE_PATH` if provided to understand existing context
- Analyze the `IDEA_INPUT` to identify the core concept and knowledge gaps
- Ask exactly ONE question at a time - never batch multiple questions
- Each subsequent question MUST build upon and reference previous answers
- Dig deep into every relevant detail: functionality, edge cases, constraints, integrations, data models, user flows, error handling, security, performance
- Track progress using TodoWrite to maintain a mental model of what's been covered
- Continue questioning until you have sufficient detail for a developer to implement without ambiguity
- When the specification is complete, synthesize all answers into a structured specification document
- Save the final specification to `requirements/<descriptive-kebab-case-name>.md`

## Workflow

1. Read `CONTEXT_FILE_PATH` if provided to gather existing context about the project or feature
2. Parse `IDEA_INPUT` to understand the initial concept and formulate the first discovery question
3. Use AskUserQuestion to ask exactly ONE focused question about the idea
4. Receive the user's answer and update your understanding
5. Determine what critical details are still missing for a complete specification
6. Formulate the next question that builds directly on the previous answer and addresses the most important gap
7. Repeat steps 3-6 until all essential details are captured:
   - Core functionality and features
   - User interactions and flows
   - Data requirements and models
   - Integration points and dependencies
   - Edge cases and error scenarios
   - Performance and scalability considerations
   - Security requirements
   - Acceptance criteria
8. When sufficient detail is gathered, synthesize all Q&A into a structured specification
9. Generate a descriptive kebab-case filename based on the feature/idea
10. Write the specification to `requirements/<generated-filename>.md`
11. Inform the user the specification is complete and where it was saved

## Report

After completing the specification, provide the user with:

- **Specification Location**: The full path to the saved specification file
- **Summary**: A brief 2-3 sentence overview of what was specified
- **Key Details Captured**: Bullet list of the main areas covered
- **Questions Asked**: Total number of discovery questions used
- **Next Steps**: Suggested actions for the developer or user (e.g., review spec, create implementation plan)

### Specification Document Format

The output specification saved to `requirements/` should follow this structure:

```markdown
# [Feature/Idea Name]

## Overview
[High-level description synthesized from the discovery process]

## Problem Statement
[What problem this solves, derived from user answers]

## Functional Requirements
[Detailed list of what the feature must do]

## User Stories / Use Cases
[Key user interactions and flows]

## Data Model
[Required data structures, entities, relationships]

## API / Interface Design
[If applicable, endpoint or interface specifications]

## Integration Points
[External systems, services, or components involved]

## Edge Cases & Error Handling
[Unusual scenarios and how to handle them]

## Security Considerations
[Authentication, authorization, data protection needs]

## Performance Requirements
[Speed, scale, resource constraints]

## Acceptance Criteria
[Specific, testable conditions for completion]

## Open Questions
[Any remaining ambiguities for developer to clarify]

## Appendix: Discovery Q&A Log
[Complete record of questions asked and answers received]
```
