---
name: mode-business-panel
description: Full business panel mode documentation. Activates on '/sc:business-panel', 'business analysis', 'expert panel', or when detailed business panel configuration is needed.
allowed-tools: Read, WebSearch, WebFetch
---

# Business Panel Mode - Full Documentation

This skill provides comprehensive documentation for the multi-expert business panel analysis system.

## Quick Reference

### Activation
- `/sc:business-panel @document.pdf`
- `--mode debate|socratic` for alternative modes
- `--experts "porter,taleb"` for specific experts

### Expert Panel (9 experts)
| Expert | Framework | Focus |
|--------|-----------|-------|
| Christensen | Jobs-to-be-Done | Innovation |
| Porter | Five Forces | Competition |
| Drucker | MBO | Management |
| Godin | Purple Cow | Marketing |
| Kim/Mauborgne | Blue Ocean | Strategy |
| Collins | Good to Great | Organization |
| Taleb | Antifragility | Risk |
| Meadows | Systems Thinking | Dynamics |
| Doumont | Structured Clarity | Communication |

### Three Phases
1. **DISCUSSION**: Collaborative multi-perspective analysis (default)
2. **DEBATE**: Stress-test through structured disagreement
3. **SOCRATIC**: Question-driven strategic thinking development

### Expert Selection by Domain
```yaml
innovation: [christensen, drucker, meadows, collins]
strategy: [porter, kim_mauborgne, collins, taleb]
marketing: [godin, christensen, doumont, porter]
risk: [taleb, meadows, porter, collins]
systems: [meadows, drucker, collins, taleb]
communication: [doumont, godin, drucker, meadows]
organization: [collins, drucker, meadows, porter]
```

For full configuration and templates, read ~/.claude/MODE_Business_Panel.md
