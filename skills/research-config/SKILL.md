---
name: research-config
description: Deep research configuration and settings. Activates on '/sc:research', 'deep research', 'research settings', or when configuring research parameters.
allowed-tools: Read, WebSearch, WebFetch
---

# Deep Research Configuration

Use this skill when you need to:
- Configure deep research parameters
- Understand research depth profiles
- Set up multi-hop patterns
- Configure source credibility rules

## Default Settings
```yaml
research_defaults:
  planning_strategy: unified
  max_hops: 5
  confidence_threshold: 0.7
  memory_enabled: true
  parallelization: true
  parallel_first: true  # MANDATORY DEFAULT
```

## Depth Profiles
| Profile | Sources | Hops | Time | Confidence |
|---------|---------|------|------|------------|
| quick | 10 | 1 | 2min | 0.6 |
| standard | 20 | 3 | 5min | 0.7 |
| deep | 40 | 4 | 8min | 0.8 |
| exhaustive | 50+ | 5 | 10min | 0.9 |

## Source Credibility Tiers
- **Tier 1** (0.9-1.0): Academic journals, official docs, peer-reviewed
- **Tier 2** (0.7-0.9): Established media, industry reports, expert blogs
- **Tier 3** (0.5-0.7): Community resources, Wikipedia, verified social
- **Tier 4** (0.3-0.5): Forums, unverified social, personal blogs

## Extraction Routing
| Content Type | Tool |
|--------------|------|
| Static HTML | Tavily |
| Dynamic/JS | Playwright |
| Technical docs | Context7 |
| Local files | Native |

## Key Rules
1. **Parallel by default**: Multiple searches, batch extractions run concurrently
2. **Sequential only for dependencies**: When Hop N requires Hop N-1 results
3. **Replanning triggers**: Confidence < 0.6, contradictions > 30%, time > 70%
4. **Memory management**: Case-based reasoning enabled, 30-day retention

For full YAML configuration, read ~/.claude/RESEARCH_CONFIG.md
