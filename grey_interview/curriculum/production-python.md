# Production Python contracts

Treat a function as a contract: accepted input, output and failure behavior. Type hints help static checking but do not validate untrusted JSON at runtime. Use Pydantic at external boundaries, dataclasses for trusted internal values and a Protocol for replaceable adapters. Keep domain logic independent of network and persistence details.

## Worked example
An account client may return Account, raise AccountNotFound for a valid missing ID, or raise DependencyUnavailable for a transient service failure. Returning None for every error destroys the distinction. Do not catch programming errors and report success.

A package can separate domain/, adapters/, service/ and tests/ without creating an abstraction for every line. A structured log event should carry operation, correlation ID, elapsed time and outcome, not a raw account record or token.

Use pytest parametrization for malformed inputs and boundary cases, fixtures for resource lifecycle, and a fake transport for deterministic client behavior. Mock your external seam, not the function under test. Include a test that would fail before a known bug fix. Run a type checker and linting alongside tests.

## Evidence gate
Produce a typed client, runtime validation, a small exception hierarchy and executed tests. Explain why each abstraction exists. Reimplement a critical operation without AI. Remove abandoned code and unused imports after revisions.

