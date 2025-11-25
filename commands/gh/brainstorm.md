---
name: gh:brainstorm
description: "ソクラテス式対話を通じて GitHub Issue 作成用の要件をインタラクティブに整理する"
category: workflow
complexity: medium
mcp-servers: [sequential, context7]
---

# /gh:brainstorm - Issue 要件ブレインストーミング

> **Purpose**: Transform ambiguous ideas into concrete GitHub Issue specifications through systematic exploration and Socratic dialogue.

---

## Behavioral Flow

### 5-Phase Process

```
1. 🔍 Explore
   ↓ Transform ambiguous ideas through Socratic dialogue

2. 🎯 Analyze
   ↓ Multi-domain analysis for comprehensive requirements

3. ✅ Validate
   ↓ Feasibility assessment and constraint identification

4. 📝 Specify
   ↓ Generate concrete specifications in Issue format

5. 🚀 Handoff
   ↓ Save to claudedocs/brainstorm/*.md → Ready for /gh:issue create
```

---

## Key Patterns

### Socratic Dialogue
**Question-driven exploration → systematic requirements discovery**

```
Phase 1: Problem Understanding
- What problem does this solve?
- Who experiences this problem?
- How are they solving it now?

Phase 2: Requirements Depth
- What's the ideal outcome?
- What are measurable success criteria?
- What constraints exist?

Phase 3: Implementation Feasibility
- What existing code is affected?
- What technical dependencies exist?
- What's the simplest viable approach?

Phase 4: Task Decomposition
- What are the logical implementation steps?
- What can be tested independently?
- What should be Phase 1 vs Phase 2?
```

### Multi-Domain Analysis
**Cross-functional expertise → comprehensive feasibility assessment**

Coordinate analysis across domains:
- **Architecture**: System design, component relationships
- **Security**: Threat modeling, access control
- **Performance**: Scalability, bottleneck identification
- **UX**: User workflows, interaction patterns
- **DevOps**: Deployment, monitoring, infrastructure

### Progressive Coordination
**Systematic exploration → iterative refinement and validation**

```
Round 1: High-level concept clarity
Round 2: Technical feasibility deep-dive
Round 3: Task breakdown and estimation
Round 4: Risk identification and mitigation
```

### Specification Generation
**Concrete requirements → actionable implementation briefs**

Output format compatible with `/gh:issue create --from-file`:

```markdown
# Feature Title

## Purpose
Clear statement of what problem this solves

## Background
- Current state
- Problem description
- Desired outcome

## Tasks
### Task 1.1: Component Name
- [ ] Specific deliverable
- [ ] Specific deliverable

### Task 1.2: Component Name
- [ ] Specific deliverable

## Technical Specifications
- Technology choices
- Architecture decisions
- Integration points

## Constraints
- Compatibility requirements
- Performance requirements
- Timeline requirements
```

---

## MCP Integration

### Sequential MCP
**Role**: Complex multi-step reasoning for systematic exploration

```yaml
sequential_usage:
  phase_1_explore:
    - Ambiguity detection in user input
    - Question generation strategy
    - Socratic dialogue structuring

  phase_2_analyze:
    - Requirement contradiction detection
    - Feasibility assessment logic
    - Domain-specific analysis coordination

  phase_3_validate:
    - Constraint validation
    - Technical feasibility verification
    - Risk assessment

  phase_4_specify:
    - Task decomposition logic
    - Dependency identification
    - Issue format structuring
```

### Context7 MCP
**Role**: Framework-specific feasibility and pattern analysis

```yaml
context7_usage:
  technology_validation:
    - Library compatibility checks
    - Framework pattern guidance
    - Best practice verification

  implementation_patterns:
    - Official documentation patterns
    - Framework-specific approaches
    - Version compatibility
```

### Serena MCP (READ-ONLY)
**Role**: Codebase understanding for context-aware requirements

```yaml
serena_usage:
  read_operations:
    - Existing architecture patterns
    - Current implementation approaches
    - Code organization conventions

  write_operations: ❌ DISABLED
    rationale: "Brainstorm results saved to files, not Serena memory"
```

---

## Tool Coordination

### Read/Write/Edit
**Requirements documentation and specification generation**

- Read existing docs for context
- Write brainstorm results to `claudedocs/brainstorm/*.md`
- Edit iteratively during refinement

### TodoWrite
**NOT USED in brainstorm phase**

- Brainstorm = requirements discovery (pre-Issue)
- TodoWrite = task execution (post-Issue creation)

### WebSearch
**Market research and technology validation**

- Competitive analysis
- Technology trend research
- Best practice discovery

### sequentialthinking
**Structured reasoning for complex requirements analysis**

- Multi-step logical reasoning
- Hypothesis generation and testing
- Systematic requirement validation

---

## File Management

### Output Location
```
claudedocs/brainstorm/
├── {feature_name}_requirements_{YYYYMMDD}.md
├── {feature_name}_requirements_{YYYYMMDD}_v2.md  # iterative refinement
└── README.md
```

### Naming Convention
```
{descriptive_feature_name}_requirements_{YYYYMMDD}.md

Examples:
- jwt_auth_requirements_20251031.md
- pipeline_commonization_requirements_20251031.md
- stripe_subscription_requirements_20251031.md
```

### .gitignore Policy
```
# claudedocs/brainstorm/.gitignore
*

# Keep only README and gitignore
!README.md
!.gitignore

# Rationale: Temporary requirements discovery artifacts
# Final specs live in GitHub Issues, not files
```

---

## Usage Examples

### Example 1: Systematic Feature Discovery
```
User: /gh:brainstorm "Add JWT authentication"

Claude: 🔍 **Phase 1: Explore**

Let's understand the authentication needs:

1. **Current State Analysis**
   - What authentication exists now?
   - What problems does it have?
   - Who are the users?

2. **Desired Outcome**
   - What should JWT enable?
   - What's the user experience?
   - What are security requirements?

User: [Answers questions]

Claude: 🎯 **Phase 2: Analyze**

Based on your responses, analyzing across domains:

**Architecture**: Token-based stateless auth
**Security**: RS256 signing, HTTPS required, XSS mitigation
**Performance**: <5ms token validation overhead
**UX**: Transparent token refresh, clear error messages

Let me check existing codebase patterns...
[Uses Serena READ-ONLY to understand current auth code]

Claude: ✅ **Phase 3: Validate**

Feasibility Assessment:
- ✅ Compatible with existing API structure
- ⚠️ Requires CORS configuration update
- ✅ Library available: jose (Native ESM)
- ⚠️ Migration strategy needed for existing users

Claude: 📝 **Phase 4: Specify**

Generating Issue specification...

[Creates structured requirement document]

Claude: 🚀 **Phase 5: Handoff**

✅ Saved: claudedocs/brainstorm/jwt_auth_requirements_20251031.md

Next steps:
$ /gh:issue create --from-file claudedocs/brainstorm/jwt_auth_requirements_20251031.md
```

### Example 2: Agile Refactoring Exploration
```
User: /gh:brainstorm "The evaluation scripts have duplicate code"

Claude: 🔍 **Exploration Questions**

1. **Scope Understanding**
   - Which scripts have duplication?
   - What code is duplicated?
   - What differs between them?

2. **Refactoring Goals**
   - What's the maintenance burden now?
   - What's the ideal structure?
   - What constraints exist?

User: [Describes 4 evaluation scripts with 450 lines of duplication]

Claude: 🎯 **Multi-Domain Analysis**

[Uses Serena to analyze actual scripts]

**Architecture**: BaseEvaluationScript inheritance exists
**Quality**: 450 lines duplicate → ~100 lines (78% reduction potential)
**Risk**: Model-specific logic must remain customizable

Claude: ✅ **Validation & Task Breakdown**

Feasible Approach: Common method in BaseEvaluationScript

Tasks:
1.1: Extract predict_gbdt() to base class
1.2: Refactor 4 scripts to use base method
1.3: Verify model-specific overrides work

Claude: 📝 **Specification Generated**

✅ Saved: claudedocs/brainstorm/pipeline_commonization_requirements_20251031.md
```

### Example 3: Complex Feature with Constraints
```
User: /gh:brainstorm "Add Stripe subscription payments"

Claude: 🔍 **Progressive Exploration**

**Round 1: Business Requirements**
- Subscription model? (monthly/annual)
- Pricing tiers?
- Free trial period?

**Round 2: Technical Constraints**
- Existing user system integration?
- Currency support?
- Payment method requirements?

**Round 3: Implementation Scope**
- Phase 1 scope? (MVP)
- Phase 2 features?
- Migration strategy?

User: [Multi-round dialogue]

Claude: 🎯 **Feasibility Analysis**

[Uses Context7 for Stripe best practices]
[Uses Serena to check existing user model]

Claude: 📝 **Phased Implementation Plan**

Phase 1 (MVP - 3 days):
- Single pricing tier
- Monthly billing only
- JPY currency only

Phase 2 (Future):
- Multiple tiers
- Annual billing
- Multi-currency

✅ Saved: claudedocs/brainstorm/stripe_subscription_requirements_20251031.md
```

---

## Integration Workflow

### What /gh:brainstorm Does

**ONLY Step 1: Requirements Discovery**
```bash
$ /gh:brainstorm
→ Interactive dialogue
→ File saved: claudedocs/brainstorm/feature_requirements_20251031.md
→ **STOPS HERE** - brainstorm is complete
```

**What brainstorm DOES NOT do:**
- ❌ Does NOT create GitHub Issues
- ❌ Does NOT start implementation
- ❌ Does NOT run any code

### What to Do Next (Manual Steps)

**Step 2: Create Issue (separate command)**
```bash
$ /gh:issue create --from-file claudedocs/brainstorm/feature_requirements_20251031.md
→ GitHub Issue #42 created
```

**Step 3: Start Implementation (separate command)**
```bash
$ /gh:issue work 42
→ Issue-driven development begins
```

**Step 4: Efficiency (optional, separate command)**
```bash
$ /sc:spawn "Issue #42の3タスクを並列実装"
→ Parallel implementation with sub-agents
```

---

## Boundaries

### Will Do ✅

- **Transform ambiguous ideas** into concrete specifications through systematic exploration
- **Ask probing questions** to uncover hidden requirements and constraints
- **Analyze feasibility** across architecture, security, performance, UX domains
- **Generate structured specs** in Issue-compatible format
- **Save to files** for explicit, trackable requirements artifacts
- **Read codebase** (via Serena) to provide context-aware requirements
- **Validate constraints** through technical feasibility assessment
- **Break down tasks** into logical, testable implementation steps

### Will Not Do ❌

- **Make implementation decisions** without proper requirements discovery
- **Override user vision** with prescriptive solutions during exploration
- **Bypass systematic exploration** for complex multi-domain projects
- **Write to Serena memory** (use files for brainstorm artifacts)
- **Start implementation** (that's for `/gh:issue work` phase)
- **Create GitHub Issues** (that's for `/gh:issue create` command)
- **Skip feasibility validation** to rush to task breakdown

---

## Best Practices

### ✅ Do

1. **Start with concrete problems**
   ```
   ✅ "Password plaintext transmission is a security risk"
   ❌ "Improve authentication"
   ```

2. **Clarify existing code relationships**
   ```
   - Replace existing auth.js?
   - Extend current system?
   - Migration path for existing users?
   ```

3. **Plan phased implementation**
   ```
   Phase 1: JWT basic implementation (MVP)
   Phase 2: Refresh tokens
   Phase 3: OAuth integration
   ```

4. **Define measurable success criteria**
   ```
   - Token validation < 5ms
   - Zero authentication errors after migration
   - 100% test coverage for auth flows
   ```

5. **Identify and document constraints**
   ```
   - Must maintain API compatibility
   - HTTPS required in production
   - Complete within 1 week
   ```

### ❌ Don't

1. **Rush to technology selection**
   - Understand problem → Define requirements → Choose technology

2. **Create oversized scope**
   ```
   ✅ 5-8 tasks per Issue (optimal, 1-3 days work)
   ⚠️  12+ tasks → Consider splitting into multiple Issues
   ❌ 15+ tasks → Definitely split (cognitive overload)

   Example - Large Feature Split:
   Issue #1: Phase 1 - Backend API (6 tasks)
   Issue #2: Phase 2 - Frontend UI (5 tasks)
   Issue #3: Phase 3 - Integration (4 tasks)
   ```
   - 1 Issue = 1 focused sprint
   - Large features → Multiple Issues

3. **Use vague success criteria**
   - Make criteria testable and measurable

4. **Ignore existing patterns**
   - Check codebase conventions first (via Serena READ)

---

## Troubleshooting

### Dialogue too long / too many questions

**Problem**: Questions keep coming, no end in sight

**Solution**:
```
"I think we have enough information. Please generate the Issue specification."
```

### Requirements too vague

**Problem**: Idea is too abstract to specify

**Solution**:
```
1. Focus on specific user problem
2. Show existing code context
3. Start with smallest viable scope
```

### Can't decide between approaches

**Problem**: Multiple valid implementation approaches

**Solution**:
```
Document alternatives in spec:

## Implementation Approaches

### Option A: JWT Library
Pros: Battle-tested, maintained
Cons: Additional dependency

### Option B: Manual Implementation
Pros: No dependencies
Cons: Security risks, maintenance burden

**Recommendation**: Option A (security-critical code)
```

### Brainstorm file not found later

**Problem**: Can't find generated file for Issue creation

**Solution**:
```bash
# List brainstorm files
$ ls claudedocs/brainstorm/

# Use absolute path
$ /gh:issue create --from-file claudedocs/brainstorm/feature_requirements_20251031.md
```

---

## Related Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/gh:brainstorm` | Requirements discovery | **Start here** for new features |
| `/gh:issue create` | Create GitHub Issue | After brainstorm file ready |
| `/gh:issue work` | Start implementation | After Issue created |
| `/gh:guide` | Complete workflow guide | Understand full process |
| `/gh:usage` | Usage patterns | See efficiency techniques |

---

## 関連コマンド

| コマンド | 用途 | 使い分け |
|---------|------|---------|
| `/gh:brainstorm` | GitHub Issue作成向け要件整理 | **このコマンド** |
| `/sc:brainstorm` | 汎用要件発見 | GitHub Issue以外のプロジェクト向け |
| `/gh:issue create` | Issue作成 | brainstormファイル準備後 |
| `/gh:issue work` | 作業開始 | Issue作成後 |
| `/gh:guide` | ワークフローガイド | 全体フロー理解 |
| `/gh:usage` | ユースケース集 | 効率的な使い方 |

---

**Last Updated**: 2025-11-25
**Version**: 1.1.0
