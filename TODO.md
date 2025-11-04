# TODO - Agentic Data Scientist

This file tracks remaining tasks for completing the Agentic Data Scientist project.

## High Priority

### Prompt Content
- [x] Fill in `prompts/base/agent_base.md` - Root agent instructions
- [x] Fill in `prompts/base/plan_generator.md` - Plan generation logic
- [x] Fill in `prompts/base/plan_orchestrator.md` - Plan orchestration logic
- [x] Fill in `prompts/base/plan_verifier.md` - Plan verification logic
- [x] Fill in `prompts/base/coding_base.md` - Coding agent instructions
- [x] Fill in `prompts/base/coding_review.md` - Review agent instructions
- [x] Fill in `prompts/base/summary.md` - Summary generation
- [x] Fill in `prompts/base/global_preamble.md` - Global context
- [x] Fill in `prompts/base/coding_planning.md` - Coding planning phase
- [ ] Fill in `prompts/domain/bioinformatics/science_methodology.md` (deferred - not needed for general-purpose version)
- [ ] Fill in `prompts/domain/bioinformatics/interactive_base.md` (deferred - not needed for general-purpose version)

### MCP Integration
- [x] Implement actual MCP server connection in `mcp/registry.py`
- [x] Add MCP client library integration
- [x] Create MCP tool wrapper for ADK Tool format
- [ ] Test with real MCP servers (filesystem, git, fetch, markitdown, claude-scientific-skills)
- [ ] Document MCP server configuration

## Medium Priority

### Testing
- [ ] Create unit tests for core API (`tests/unit/test_core_api.py`)
- [ ] Create unit tests for agents (`tests/unit/test_agents.py`)
- [ ] Create unit tests for events (`tests/unit/test_events.py`)
- [ ] Create integration tests for end-to-end flows (`tests/integration/`)
- [ ] Create integration tests for MCP (`tests/integration/test_mcp.py`)
- [ ] Set up pytest fixtures and test data

### Documentation
- [ ] Create `docs/getting_started.md` - Quick start guide
- [ ] Create `docs/api_reference.md` - API documentation
- [ ] Create `docs/mcp_configuration.md` - MCP setup guide
- [ ] Create `docs/extending.md` - Extension/customization guide
- [ ] Add architecture diagrams
- [ ] Add usage examples to docs

## Low Priority

### Code Quality
- [ ] Run `ruff format` on all Python files
- [ ] Run `ruff check --fix` to fix linting issues
- [ ] Add type hints where missing
- [ ] Improve error messages and logging
- [ ] Add more inline documentation

### Package Management
- [ ] Test package installation with pip
- [ ] Test CLI with uvx
- [ ] Verify all imports work correctly
- [ ] Test in fresh virtual environment
- [ ] Create CHANGELOG.md

### Examples & Demos
- [ ] Add example with file handling
- [ ] Add example with custom MCP configuration
- [ ] Add example for multi-step data analysis
- [ ] Create tutorial notebook (optional)

### Infrastructure
- [ ] Set up CI/CD pipeline
- [ ] Add GitHub Actions for tests
- [ ] Add automated linting checks
- [ ] Set up automatic release process
- [ ] Add contribution guidelines

## Future Enhancements

- [ ] Add more agent types (if needed)
- [ ] Create plugin system for custom prompts
- [ ] Add web UI (optional)
- [ ] Performance optimization
- [ ] Add caching for repeated queries
- [ ] Support for conversation persistence
- [ ] Multi-user session management

## Notes

- All critical blockers from the original migration have been resolved
- Loop detection module is in place
- Prompt template structure is ready for content
- All imports and references have been updated
- Package is ready for development and testing

