# LinBlock Test Strategy

Version: 1.0.0
Status: Draft
Last Updated: 2025-01-28
Owner: Agent 009 (QA Lead)

---

## 1. Overview

This document defines the comprehensive testing strategy for the LinBlock Android emulator project. It covers testing levels, tooling, coverage requirements, CI integration, and quality gates that all contributors must follow.

### 1.1 Goals

- Catch defects early through automated testing at every layer
- Maintain high code quality through linting and static analysis
- Ensure performance targets are met through benchmark suites
- Enable confident refactoring via comprehensive regression coverage
- Support parallel development with isolated, mockable module tests

### 1.2 Guiding Principles

1. **Test the interface, not the implementation** -- Tests validate the public API defined in each module's `INTERFACE.md`
2. **Isolation by default** -- Unit tests mock all dependencies; no cross-module calls
3. **Deterministic results** -- Tests must not depend on timing, network, or external state
4. **Fast feedback** -- Unit tests complete in under 60 seconds total
5. **Pyramid shape** -- Many unit tests, fewer integration tests, fewest E2E tests

---

## 2. Testing Levels

### 2.1 Unit Tests

**Scope:** Individual modules tested in complete isolation. All dependencies are mocked.

| Attribute       | Detail                                           |
|-----------------|--------------------------------------------------|
| Location        | `tests/unit/test_{module_name}.py`               |
| Dependencies    | All mocked via `mocks/mock_interface.py`         |
| Execution time  | < 1 second per test                              |
| Trigger         | Every push, every PR                             |
| Coverage target | >= 70% per module (80% target)                   |

Each module provides its own mock implementation. Unit tests import mocks from the module's `mocks/` directory and verify behavior against the interface contract.

**Example structure:**
```
tests/unit/
    conftest.py
    test_config_manager.py
    test_log_manager.py
    test_event_bus.py
    test_emulator_core.py
    test_display_manager.py
    ...
```

### 2.2 Integration Tests

**Scope:** Cross-module interactions. Verifies that real module implementations work together correctly through their defined interfaces.

| Attribute       | Detail                                           |
|-----------------|--------------------------------------------------|
| Location        | `tests/integration/test_{layer}_integration.py`  |
| Dependencies    | Real implementations for modules under test      |
| Execution time  | < 10 seconds per test                            |
| Trigger         | PR to main, nightly builds                       |
| Coverage target | Critical paths between modules                   |

Integration tests focus on layer boundaries:
- Infrastructure layer: config_manager + log_manager + event_bus
- Emulation layer: emulator_core + cpu_emulator + memory_manager
- Android layer: android_runtime + system_image_manager + app_manager
- GUI layer: gui_framework + display_manager + input_manager

### 2.3 System / End-to-End Tests

**Scope:** Full system behavior with a real Android system image. Validates user-facing workflows from GUI launch to Android app execution.

| Attribute       | Detail                                           |
|-----------------|--------------------------------------------------|
| Location        | `tests/e2e/test_{scenario}.py`                   |
| Dependencies    | Full running system, real AOSP image             |
| Execution time  | Minutes per scenario                             |
| Trigger         | Pre-release, nightly on develop                  |
| Coverage target | Critical user journeys                           |

Scenarios include:
- Cold boot to home screen
- App installation and launch
- Input interaction (touch, keyboard, gamepad)
- Snapshot save and restore
- Multi-instance management

### 2.4 Performance Tests

**Scope:** Quantitative measurement of system performance against defined benchmarks.

| Attribute       | Detail                                           |
|-----------------|--------------------------------------------------|
| Location        | `tests/performance/benchmark_{metric}.py`        |
| Dependencies    | Full or partial system                           |
| Execution time  | Variable (seconds to minutes)                    |
| Trigger         | Pre-release, weekly on develop                   |

Performance benchmarks (see Section 7 for details):
- Boot time
- Frame rate
- Memory usage
- Input latency

### 2.5 Security Tests

**Scope:** Validate that the emulator sandbox is properly isolated, no privilege escalation paths exist, and sensitive data is protected.

| Attribute       | Detail                                           |
|-----------------|--------------------------------------------------|
| Location        | `tests/security/test_{concern}.py`               |
| Dependencies    | Full system                                      |
| Execution time  | Variable                                         |
| Trigger         | Pre-release, monthly audit                       |

Security test areas:
- Sandbox isolation (host filesystem access restrictions)
- Network isolation (no unintended host network exposure)
- Privilege escalation checks
- Input validation and sanitization
- Configuration file permission validation

---

## 3. Frameworks and Tooling

### 3.1 Test Framework

| Tool        | Purpose                          | Version   |
|-------------|----------------------------------|-----------|
| **pytest**  | Test runner and framework        | >= 8.0    |
| **pytest-cov** | Coverage measurement         | >= 4.0    |
| **pytest-xdist** | Parallel test execution    | >= 3.0    |
| **pytest-mock** | Mock/patch utilities         | >= 3.0    |

### 3.2 Static Analysis

| Tool        | Purpose                          | Version   |
|-------------|----------------------------------|-----------|
| **flake8**  | PEP 8 style enforcement         | >= 7.0    |
| **mypy**    | Static type checking             | >= 1.0    |
| **bandit**  | Security-focused linting         | >= 1.7    |

### 3.3 Configuration

**pytest.ini / pyproject.toml markers:**
```ini
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (isolated, mocked dependencies)",
    "integration: Integration tests (cross-module)",
    "e2e: End-to-end system tests",
    "performance: Performance benchmarks",
    "security: Security validation tests",
    "slow: Tests that take more than 5 seconds",
]
testpaths = ["tests"]
```

**flake8 configuration:**
```ini
[flake8]
max-line-length = 120
exclude = .git,__pycache__,build,dist,vendor
per-file-ignores =
    __init__.py:F401
```

---

## 4. Coverage Targets

### 4.1 Minimum Requirements

| Metric                    | Minimum | Target | Stretch |
|---------------------------|---------|--------|---------|
| Per-module line coverage  | 70%     | 80%    | 90%     |
| Per-module branch coverage| 60%     | 70%    | 80%     |
| Overall project coverage  | 70%     | 80%    | 85%     |

### 4.2 Coverage Enforcement

- Coverage is measured on every CI run via `pytest-cov`
- Coverage reports are uploaded as CI artifacts
- PRs that drop any module below 70% line coverage are blocked
- Coverage trends are tracked over time; regressions require justification

### 4.3 Excluded from Coverage

- `__init__.py` files (import-only)
- `mocks/` directories
- `vendor/` directory
- Generated code
- Type stubs (`.pyi` files)

---

## 5. CI Integration

### 5.1 GitHub Actions Pipeline

Every push and pull request triggers the CI pipeline defined in `.github/workflows/ci.yml`.

**Pipeline stages:**

```
Push / PR
    |
    v
[1. Lint]  -----> flake8 src/ tests/
    |              mypy src/
    v
[2. Unit Tests] -> pytest tests/unit/ --cov
    |              Upload coverage artifact
    v
[3. Import Check] -> Verify all layer __init__.py imports
    |
    v
[Pass / Fail]
```

### 5.2 Trigger Rules

| Event              | Stages Run                                |
|--------------------|-------------------------------------------|
| Push to main       | lint, unit tests, import check            |
| Push to develop    | lint, unit tests, import check            |
| PR to main         | lint, unit tests, import check            |
| Nightly (cron)     | All above + integration + performance     |
| Pre-release (tag)  | All above + E2E + security                |

### 5.3 Failure Handling

- Any lint failure blocks the pipeline
- Any unit test failure blocks the pipeline
- Coverage below 70% on any module blocks merge to main
- Performance regressions generate warnings but do not block (until Phase B)

---

## 6. Test Naming and Organization

### 6.1 Naming Convention

All test functions follow the pattern:

```
test_{description}
```

Where `{description}` clearly states what is being tested and the expected outcome.

**Examples:**
```python
def test_config_load_returns_dict():
def test_config_load_missing_file_raises_error():
def test_event_bus_dispatch_calls_all_handlers():
def test_boot_time_under_thirty_seconds():
```

### 6.2 Test File Naming

Each module's tests live in a single file per test level:

```
tests/unit/test_{module_name}.py
tests/integration/test_{layer}_integration.py
tests/performance/benchmark_{metric}.py
tests/security/test_{concern}.py
```

### 6.3 Test Class Usage

Test classes group related tests. Class names use `Test{Feature}`:

```python
class TestConfigLoad:
    def test_load_valid_file(self): ...
    def test_load_missing_file(self): ...
    def test_load_corrupt_file(self): ...
```

---

## 7. Fixture Strategy

### 7.1 Fixture Hierarchy

```
tests/
    conftest.py              # Root: shared fixtures (project_root, sample_config)
    unit/
        conftest.py          # Unit: isolation utilities, common mocks
    integration/
        conftest.py          # Integration: infrastructure_config, layer setups
    performance/
        conftest.py          # Performance: benchmark_timer, resource monitors
    security/
        conftest.py          # Security: sandbox fixtures, isolation checks
```

### 7.2 Root conftest.py

Provides fixtures available to ALL tests:
- `project_root` -- absolute path to project root
- `empty_config` -- empty configuration dict
- `sample_config` -- basic configuration for quick tests

### 7.3 Level-Specific conftest.py

Each test level directory has its own `conftest.py` with fixtures specific to that testing level. Fixtures in child directories override root fixtures with the same name.

### 7.4 Fixture Scope Guidelines

| Scope      | Use Case                                         |
|------------|--------------------------------------------------|
| `function` | Default. Fresh fixture per test function.        |
| `class`    | Shared state within a test class (read-only).    |
| `module`   | Expensive setup shared across a test file.       |
| `session`  | System-level resources (e.g., emulator process). |

---

## 8. Mock Strategy

### 8.1 Module-Level Mocks

Every module provides its own mock implementation in:

```
src/modules/{layer}/{module_name}/mocks/mock_interface.py
```

This mock implements the same interface as the real module but returns deterministic, controllable data. Other modules import these mocks for their own unit tests.

### 8.2 Mock Requirements

1. Mocks MUST implement the same public interface as the real module
2. Mocks MUST be stateless by default (configurable for specific test scenarios)
3. Mocks MUST return deterministic values
4. Mocks MUST raise the same exceptions as the real module for error cases
5. Mocks SHOULD support call recording for assertion purposes

### 8.3 Mock Example

```python
# src/modules/infrastructure/config_manager/mocks/mock_interface.py
class MockConfigManager:
    """Mock implementation of ConfigManager for unit testing."""

    def __init__(self, config_data=None):
        self._data = config_data or {}
        self.calls = []

    def load(self, path: str) -> dict:
        self.calls.append(("load", path))
        return self._data.copy()

    def save(self, path: str, data: dict) -> None:
        self.calls.append(("save", path, data))
        self._data = data.copy()
```

### 8.4 When NOT to Mock

- Integration tests: use real implementations for modules under test
- E2E tests: no mocks at all
- Performance tests: real implementations only

---

## 9. Performance Benchmarks

### 9.1 Benchmark Targets

| Metric            | Target     | Maximum Acceptable | Measured By                |
|-------------------|------------|---------------------|----------------------------|
| Cold boot time    | < 20s      | < 30s               | Time from start to home screen |
| Frame rate        | 30 fps     | >= 24 fps            | Average over 60s session   |
| Memory (idle)     | < 3 GB     | < 4 GB               | RSS after boot, idle 30s   |
| Memory (active)   | < 3.5 GB   | < 4 GB               | RSS during app execution   |
| Input latency     | < 30 ms    | < 50 ms              | Touch event to screen update |
| Snapshot save     | < 5s       | < 10s                | Time to write state to disk |
| Snapshot restore  | < 10s      | < 15s                | Time from restore to usable |

### 9.2 Benchmark Execution

Benchmarks run on standardized hardware profiles:
- **Minimum spec:** 4-core CPU, 8 GB RAM, integrated GPU
- **Recommended spec:** 8-core CPU, 16 GB RAM, dedicated GPU

Benchmark results are recorded as JSON and tracked over time. Any regression > 10% from the previous baseline triggers a warning.

### 9.3 Benchmark Files

```
tests/performance/
    conftest.py                 # Benchmark utilities
    benchmark_boot.py           # Boot time measurement
    benchmark_framerate.py      # Frame rate measurement
    benchmark_memory.py         # Memory usage measurement
    benchmark_input_latency.py  # Input latency measurement (future)
```

---

## 10. Quality Gates

### 10.1 Before Merge (PR to main)

All of the following must pass:

| Gate                          | Requirement                           |
|-------------------------------|---------------------------------------|
| All unit tests pass           | 0 failures                            |
| Line coverage per module      | >= 70%                                |
| No critical lint errors       | flake8 returns 0                      |
| Type check passes             | mypy returns 0 (when enabled)         |
| No new security warnings      | bandit returns 0 high-severity        |
| PR review approved            | At least 1 approval                   |

### 10.2 Before Release (tag)

All merge gates plus:

| Gate                          | Requirement                           |
|-------------------------------|---------------------------------------|
| All integration tests pass    | 0 failures                            |
| Performance targets met       | All benchmarks within acceptable      |
| Security tests pass           | 0 failures                            |
| 4-hour stability test         | No crashes, no memory leaks           |
| E2E critical paths pass       | All user journey scenarios green      |
| Changelog updated             | CHANGELOG.md reflects all changes     |
| Documentation current         | API docs match implementation         |

### 10.3 Nightly Build Gates

| Gate                          | Requirement                           |
|-------------------------------|---------------------------------------|
| All unit + integration pass   | 0 failures                            |
| Performance benchmarks run    | Results recorded, regressions flagged |
| Coverage trend check          | No module dropped below 70%           |

---

## 11. Test Pyramid

```
                /\
               /  \
              / E2E\           ~5% of tests
             / (few) \         Full system, real images
            /----------\
           /            \
          / Integration   \    ~15% of tests
         / (moderate)      \   Cross-module, real impls
        /-------------------\
       /                     \
      /     Unit Tests        \  ~80% of tests
     /     (many, fast)        \ Isolated, all mocked
    /___________________________\
```

### 11.1 Distribution Guidelines

- **Unit tests:** Write for every public method in every module. Aim for 5-20 tests per module depending on complexity.
- **Integration tests:** Write for every cross-module interaction defined in architecture. Aim for 3-10 tests per layer boundary.
- **E2E tests:** Write for critical user journeys only. Aim for 5-15 scenarios total covering the most important workflows.

### 11.2 When to Add Tests

- **New module:** Unit tests required before merge. Integration tests required within one sprint.
- **Bug fix:** Regression test required (unit or integration depending on scope).
- **New feature:** Unit tests required. Integration test required if cross-module.
- **Performance change:** Benchmark update required.

---

## 12. Test Data Management

### 12.1 Test Data Location

```
tests/
    fixtures/           # Shared test data files
        configs/        # Sample configuration files
        images/         # Small test images for display tests
        apks/           # Minimal test APK files
```

### 12.2 Test Data Guidelines

- Test data files must be small (< 1 MB each)
- No production data or credentials in test fixtures
- Large test assets (system images) are downloaded on demand, not committed
- Test data is version-controlled alongside tests

---

## 13. Appendix

### 13.1 Running Tests Locally

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=term-missing

# Run specific module tests
pytest tests/unit/test_config_manager.py -v

# Run integration tests
pytest tests/integration/ -v

# Run performance benchmarks
pytest tests/performance/ -v -m performance

# Run lint
flake8 src/ tests/

# Run type check
mypy src/
```

### 13.2 Writing a New Test

1. Identify the module and its public interface
2. Create `tests/unit/test_{module_name}.py`
3. Import mocks from `src/modules/{layer}/{module}/mocks/mock_interface.py`
4. Write test functions: `test_{description}`
5. Add fixtures to `tests/unit/conftest.py` if reusable
6. Verify coverage: `pytest tests/unit/test_{module_name}.py --cov=src/modules/{layer}/{module}`

### 13.3 References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [flake8 documentation](https://flake8.pycqa.org/)
- [mypy documentation](https://mypy.readthedocs.io/)
- LinBlock Modular Architecture: `docs/design/modular_architecture.md`
- LinBlock Module Template: `docs/design/module_template.md`
