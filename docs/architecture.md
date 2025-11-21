# Architecture and Technical Design

This document explains the technical internals, design decisions, and implementation details of Agentic Data Scientist.

## Table of Contents

- [Agent Hierarchy](#agent-hierarchy)
- [Workflow Design Rationale](#workflow-design-rationale)
- [Context Window Management](#context-window-management)
- [Event Compression System](#event-compression-system)
- [Loop Detection](#loop-detection)
- [Stage Orchestration](#stage-orchestration)
- [Review Confirmation Logic](#review-confirmation-logic)
- [Performance Considerations](#performance-considerations)

## Agent Hierarchy

The ADK workflow consists of multiple specialized agents organized into a hierarchical structure:

```
Workflow Root (SequentialAgent)
├── Planning Loop (NonEscalatingLoopAgent)
│   ├── Plan Maker (LoopDetectionAgent)
│   ├── Plan Reviewer (LoopDetectionAgent)
│   └── Plan Review Confirmation (LoopDetectionAgent)
├── Plan Parser (LoopDetectionAgent)
├── Stage Orchestrator (Custom Agent)
│   └── For each stage:
│       ├── Implementation Loop (NonEscalatingLoopAgent)
│       │   ├── Coding Agent (ClaudeCodeAgent)
│       │   ├── Review Agent (LoopDetectionAgent)
│       │   └── Implementation Review Confirmation (LoopDetectionAgent)
│       ├── Criteria Checker (LoopDetectionAgent)
│       └── Stage Reflector (LoopDetectionAgent)
└── Summary Agent (LoopDetectionAgent)
```

### Agent Types

**LoopDetectionAgent**
- Extends ADK's LlmAgent with automatic loop detection
- Monitors output for repetitive patterns
- Prevents infinite generation by detecting when agent is stuck
- Used for all LLM-based planning and review agents

**ClaudeCodeAgent**
- Wraps Claude Code SDK for implementation work
- Has access to 380+ scientific Skills
- Provides file system and code execution capabilities
- Sandboxed to working directory for security

**NonEscalatingLoopAgent**
- Manages iterative refinement without escalation
- Allows multiple rounds of feedback without failing the workflow
- Used for planning loop and implementation loop
- Prevents rejection signals from propagating upward

**StageOrchestratorAgent**
- Custom orchestrator managing stage-by-stage execution
- Coordinates implementation loop, criteria checking, and reflection
- Handles adaptive replanning based on progress
- Maintains stage state and success criteria tracking

## Workflow Design Rationale

### Why Separate Planning from Execution?

**Problem:** Direct implementation often misses requirements, leading to rework and incomplete results.

**Solution:** Dedicated planning phase with validation
- Plan Maker focuses solely on comprehensive planning
- Plan Reviewer provides independent validation
- Success criteria established before any implementation
- Issues caught early when they're cheapest to fix

**Trade-off:** Extra API calls and time, but significantly higher quality results.

### Why Iterative Refinement?

**Problem:** Single-pass planning and implementation often have quality issues.

**Solution:** Multiple review loops at both planning and implementation stages
- Planning loop: Iterate until plan is complete and validated
- Implementation loop: Iterate until code meets requirements
- Each iteration improves quality incrementally

**Mechanism:** NonEscalatingLoopAgent allows multiple rounds without failure escalation.

### Why Adaptive Replanning?

**Problem:** Rigid plans can't accommodate discoveries made during implementation.

**Solution:** Stage Reflector adapts remaining stages after each implementation
- Analyzes what was accomplished
- Identifies what's still needed
- Modifies or extends remaining stages
- Ensures final deliverable meets actual needs

**Benefit:** Plans evolve based on reality, not just initial assumptions.

### Why Continuous Validation?

**Problem:** Hard to track progress objectively in multi-stage workflows.

**Solution:** Criteria Checker updates success criteria after each stage
- Inspects generated files and results
- Updates which criteria are now met
- Provides objective evidence of progress
- Clear visibility into what remains

**Benefit:** Objective measurement prevents unclear progress and missed requirements.

## Context Window Management

The framework implements aggressive context management to handle long-running analyses within model token limits.

### The Challenge

Multi-stage analyses can generate hundreds of events:
- Each agent turn adds multiple events (messages, tool calls, responses)
- Events accumulate throughout the workflow
- Without management, context would exceed 1M token limit
- Token overflow causes workflow failures

### Strategy Overview

Multiple layers of protection:
1. **Callback-based compression**: Automatic after each agent turn
2. **Manual compression**: Triggered at key orchestration points
3. **Hard limit trimming**: Emergency fallback
4. **Large text truncation**: Prevents individual events from consuming excessive tokens

### Event Compression System

#### How It Works

The compression system uses LLM-based summarization to preserve critical context while removing old events:

1. **Threshold Detection**: Monitors event count after each agent turn
2. **Summary Generation**: When threshold exceeded, LLM summarizes old events
3. **Event Replacement**: Old events replaced with single summary event
4. **Truncation**: Remaining events have large text truncated (>5KB)
5. **Direct Assignment**: Uses `session.events = new_events` to ensure ADK recognizes changes

#### Key Implementation Details

```python
# Compression triggered when events exceed threshold
if len(events) > EVENT_THRESHOLD:
    # Summarize old events using LLM
    summary = await generate_summary(old_events)
    
    # Replace old events with summary
    new_events = [summary_event] + recent_events
    
    # Truncate large text in remaining events
    truncated_events = truncate_large_text(new_events)
    
    # Direct assignment (not append/pop) to ensure ADK sees change
    session.events = truncated_events
```

#### Why Direct Assignment?

Initial implementation used `pop()` operations, but ADK's session service didn't recognize the changes. Direct list assignment (`session.events = new_events`) forces ADK to update the context properly.

#### Compression Parameters

- **EVENT_THRESHOLD**: 30 events (when compression triggers)
- **EVENT_OVERLAP**: 10 events (kept as recent context)
- **MAX_EVENTS**: 50 events (hard limit for emergency trimming)
- **TRUNCATE_SIZE**: 5000 characters (max size for event text)

These aggressive defaults ensure context stays manageable even during complex analyses.

### Preventing Token Overflow

#### Callback-based Compression

```python
def compression_callback(session):
    """Called after each agent turn."""
    if len(session.events) > EVENT_THRESHOLD:
        compress_events(session)
```

Automatically triggered by ADK's callback system.

#### Manual Compression

```python
# After implementation loop completes
await compress_session_events(session, force=True)
```

Called at key orchestration points (e.g., after implementation loop, before reflection).

#### Hard Limit Trimming

```python
if len(session.events) > MAX_EVENTS:
    # Emergency: discard oldest events
    session.events = session.events[-MAX_EVENTS:]
```

Safety mechanism when compression isn't sufficient.

#### Large Text Truncation

```python
def truncate_event_text(event, max_size=5000):
    """Truncate large text content in events."""
    if len(event.text) > max_size:
        event.text = event.text[:max_size] + "... [truncated]"
    return event
```

Prevents individual events from consuming excessive tokens.

### Why This Matters

Without aggressive compression:
- Complex analyses would exceed 1M token limit
- Workflows would fail partway through
- Users would lose hours of progress

With compression:
- Analyses can run for hours with hundreds of events
- Total context stays under 1M tokens
- Workflows complete successfully

## Loop Detection

### The Problem

LLM agents can sometimes enter infinite loops:
- Repeating the same output
- Getting stuck in circular reasoning
- Generating endless variations of the same content

### The Solution

LoopDetectionAgent monitors output for repetitive patterns:

```python
class LoopDetectionAgent(LlmAgent):
    def __init__(self, min_pattern_length=200, repetition_threshold=3):
        self.min_pattern_length = min_pattern_length
        self.repetition_threshold = repetition_threshold
        self.output_history = []
    
    def detect_loop(self, new_output):
        """Detect if output is repeating."""
        self.output_history.append(new_output)
        
        # Check for repeated patterns
        for i in range(len(self.output_history) - 1):
            if self.is_similar(self.output_history[i], new_output):
                repetition_count += 1
        
        if repetition_count >= self.repetition_threshold:
            raise LoopDetectedError("Agent is repeating itself")
```

### Parameters

- **min_pattern_length**: Minimum text length to consider (default: 200 chars)
- **repetition_threshold**: Number of repetitions before triggering (default: 3)

### Why It Works

- Catches stuck agents before they consume excessive tokens
- Allows legitimate iteration while preventing infinite loops
- Tunable thresholds for different agent types

## Stage Orchestration

### The StageOrchestratorAgent

Custom agent that manages stage-by-stage execution:

```python
class StageOrchestratorAgent:
    async def run_stage(self, stage):
        # 1. Implementation Loop
        implementation = await self.run_implementation_loop(stage)
        
        # 2. Compress events (manual)
        await compress_session_events(self.session)
        
        # 3. Check Success Criteria
        criteria_update = await self.check_criteria()
        
        # 4. Reflect and Adapt
        adapted_stages = await self.reflect_on_progress()
        
        return adapted_stages
```

### Stage Flow

1. **Implementation Loop**
   - Coding Agent implements the stage
   - Review Agent validates implementation
   - Review Confirmation decides to continue or exit loop
   - Repeats until implementation approved

2. **Event Compression**
   - Manual compression after implementation loop
   - Prevents context overflow from long implementations
   - Preserves critical context via summarization

3. **Criteria Checking**
   - Criteria Checker inspects generated files
   - Updates which success criteria are now met
   - Provides objective evidence of progress

4. **Reflection and Adaptation**
   - Stage Reflector analyzes progress
   - Identifies what still needs to be done
   - Modifies or extends remaining stages
   - Returns adapted stage list

### Why This Design?

**Separation of Concerns**: Each sub-agent has a focused responsibility
**Explicit Compression**: Manual compression at key points ensures context management
**Adaptive Planning**: Reflection after each stage allows plan adaptation
**Objective Progress**: Criteria checking provides measurable progress

## Review Confirmation Logic

### The Challenge

How does the workflow decide when to exit review loops?

### The Solution

Dedicated confirmation agents that parse review feedback and make exit decisions:

```python
class ReviewConfirmationAgent(LoopDetectionAgent):
    """Decides whether to exit review loop."""
    
    instruction = """
    Review the feedback and decide:
    - exit: true if approved, false if needs revision
    - reason: explanation for decision
    
    Output JSON: {"exit": true/false, "reason": "..."}
    """
```

### How It Works

1. **Plan Review Confirmation**
   - Receives plan and review feedback
   - Decides if plan is complete enough to proceed
   - Outputs structured decision: `{"exit": true, "reason": "..."}`

2. **Implementation Review Confirmation**
   - Receives implementation and review feedback
   - Decides if implementation meets requirements
   - Outputs structured decision: `{"exit": true, "reason": "..."}`

### Why Structured Output?

- Explicit decision point in the workflow
- Clear reason for approval/rejection
- Easy to parse and log
- Prevents ambiguous loop exit conditions

### Exit Conditions

**Exit Loop (approve):**
- Review feedback is positive
- Requirements are met
- No major issues found

**Continue Loop (reject):**
- Review found issues
- Requirements not fully met
- Needs revision

## Performance Considerations

### Token Usage

**Planning Phase**: 10k-50k tokens
- Multiple iterations of plan creation and review
- Structured output generation
- File inspection

**Implementation Phase per Stage**: 50k-200k tokens
- Multiple iterations of implementation and review
- Code generation and execution
- File operations and inspections

**Total for Complex Analysis**: 500k-1M tokens
- Multiple stages
- Event compression keeps it under limit
- Worth it for quality results

### Latency

**Orchestrated Mode**: 5-30 minutes for complex analyses
- Planning: 1-3 minutes
- Implementation: 2-10 minutes per stage
- Review and validation: 1-2 minutes per iteration

**Simple Mode**: 30 seconds - 5 minutes
- No planning overhead
- Single implementation pass
- No validation loops

### Cost

**Orchestrated Mode**: $1-10 per analysis (varies by complexity)
- Multiple LLM calls
- Planning and review agents (via OpenRouter)
- Coding agent (Claude Sonnet 4.5)

**Simple Mode**: $0.10-1 per task
- Single coding agent call
- No planning/review overhead

### When Cost is Worth It

**Use Orchestrated Mode For:**
- Production analyses
- Complex multi-stage workflows
- Critical business decisions
- Situations where mistakes are expensive

**Use Simple Mode For:**
- Quick explorations
- Simple scripts
- Learning and development
- Budget-conscious work

## Memory Management

### Working Directory Isolation

Each session gets its own working directory:
- Agents sandboxed to their directory
- No cross-session file access
- Automatic cleanup for temp directories
- Preserved for project directories

### Session State

State stored in ADK session:
```python
session.state = {
    'high_level_plan': "...",
    'high_level_stages': [...],
    'high_level_success_criteria': [...],
    'stage_implementations': [...],
    'current_stage': {...},
}
```

All agents access shared state for coordination.

### Event Queue

Events stored in session:
- Message events (agent output)
- Function call events (tool usage)
- Function response events (tool results)
- Usage events (token counts)

Managed via compression to stay under limits.

## Error Handling

### Escalation Strategy

**NonEscalatingLoopAgent**: Catches rejections without escalating
- Allows iterative refinement
- Prevents single rejection from failing workflow

**LoopDetectionAgent**: Escalates when stuck
- Detects infinite loops
- Prevents wasted resources

**StageOrchestrator**: Handles stage failures gracefully
- Logs errors
- Can retry or skip stages
- Provides informative error messages

### Recovery Mechanisms

1. **Retry Logic**: Failed stages can be retried
2. **Graceful Degradation**: Partial results returned on failure
3. **Error Context**: Full error details logged for debugging
4. **State Preservation**: Session state preserved for analysis

## Design Principles

1. **Separation of Concerns**: Each agent has one clear responsibility
2. **Explicit Over Implicit**: Clear decision points and state transitions
3. **Iterative Refinement**: Multiple passes improve quality
4. **Objective Validation**: Measurable success criteria
5. **Context Management**: Aggressive compression for long workflows
6. **Fail-Fast for Loops**: Detect and exit infinite loops quickly
7. **Fail-Gracefully for Stages**: Handle errors without losing progress

## Future Improvements

Potential areas for enhancement:

**Parallel Stage Execution**: Run independent stages concurrently
**Streaming Compression**: Compress while streaming to users
**Adaptive Thresholds**: Adjust compression based on token usage
**Stage Checkpointing**: Save/resume from any stage
**Cost Optimization**: Selectively use cheaper models for certain tasks

