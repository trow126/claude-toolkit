---
name: business-panel-examples
description: Show usage examples for /sc:business-panel command. Includes expert selection strategies, output formats, integration workflows.
allowed-tools: Read
---

# Business Panel Usage Examples

Use this skill when you need to:
- Show examples of /sc:business-panel usage
- Demonstrate expert selection strategies
- Explain output format variations
- Guide integration workflows

## Quick Reference

### Basic Commands
```bash
/sc:business-panel @doc.pdf                          # Default analysis
/sc:business-panel @doc.pdf --mode debate            # Challenge mode
/sc:business-panel @doc.pdf --mode socratic          # Learning mode
/sc:business-panel @doc.pdf --experts "porter,taleb" # Specific experts
```

### Expert Selection by Domain
| Domain | Recommended Experts |
|--------|---------------------|
| Strategy | porter, kim_mauborgne, collins, meadows |
| Innovation | christensen, drucker, godin, meadows |
| Risk | taleb, meadows, porter, collins |
| Marketing | godin, christensen, doumont, porter |
| Organization | collins, drucker, meadows, porter |

### Output Formats
- `--structured`: Executive summary format
- `--verbose`: Framework-by-framework detail
- `--questions`: Question-driven exploration
- `--synthesis-only`: Cross-framework synthesis only

### Integration Patterns
```bash
/analyze @doc.md --business-panel    # Technical + business analysis
/improve @doc.md --business-panel    # Iterative improvement
/design system --business-panel      # Design with expert guidance
```

For detailed examples and workflows, see MODE_Business_Panel.md.
