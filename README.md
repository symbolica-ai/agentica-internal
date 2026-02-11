![Header image](assets/Header.png)

# Agentica Internal Libraries

[![PyPI version](https://img.shields.io/pypi/v/agentica-internal.svg)](https://pypi.org/project/agentica-internal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Discord](https://img.shields.io/discord/1470799122717085941?logo=discord&label=Discord)](https://discord.gg/bddGs8bb)
[![Twitter](https://img.shields.io/twitter/follow/symbolica?style=flat&logo=x&label=Follow)](https://x.com/symbolica)

[Agentica](https://agentica.symbolica.ai) is a type-safe AI framework that lets LLM agents integrate with your code—functions, classes, live objects, even entire SDKs. Instead of building MCP wrappers or brittle schemas, you pass references directly; the framework enforces your types at runtime, constrains return types, and manages agent lifecycle.

## Overview

This package contains internal shared libraries for the Agentica framework. This package provides the foundational components used by both the client SDKs and session manager, including communication protocols, Python execution environments, and telemetry infrastructure.

The following may be found here:
- **Protocol definitions** for HTTP and WebSocket communication
- **Python REPL** with custom evaluation semantics
- **Remote procedure call** system for distributed Python object access
- **Telemetry** with OpenTelemetry integration
- **Core utilities** shared across all components

See also:
- [The Agentica Python SDK](https://github.com/symbolica-ai/agentica-python-sdk)
- [The Agentica TypeScript SDK](https://github.com/symbolica-ai/agentica-typescript-sdk)
- [The Agentica Server](https://github.com/symbolica-ai/agentica-server)

## Package Structure

### Communication Protocols

#### `session_manager_messages/`
HTTP-based protocol for initial client-server interactions and telemetry events.

See there for:
- Agent creation and configuration messages
- OpenTelemetry span definitions following [GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- Distributed tracing with trace context propagation
- Structured logging payloads for code execution and results

#### `multiplex_protocol/`
WebSocket-based bidirectional messaging protocol for agent invocations.

See there for:
- Invoke, cancel, and stream messages
- Error propagation with typed exception hierarchies
- Timestamped event tracking, parent-child tracking

#### `invocation_protocol/`
Higher-level abstraction for agent invocation messages.

See there for:
- Type-safe message definitions using `msgspec`
- Client/server message type unions
- Invocation lifecycle events (ENTER, EXIT, ERROR)
- Warp payload handling for distributed Python objects

### Python Execution

#### `repl/`
Self-contained Python REPL with enhanced capabilities.

See there for:
- Top-level `await` support with event loop integration
- Automatic printing of last expression in multi-line blocks
- Custom `import` semantics and module interception
- Temporary stdio redirection during evaluation
- Enhanced stack traces and error formatting
- Variable tracking and diff generation
- Evaluation history and session management

Main classes:
- `BaseRepl` - Core REPL implementation
- `ReplEvaluationInfo` - Metadata about code evaluation
- `ReplVars` - Variable namespace management
- `ReplCode` - Code compilation with custom options

#### `cpython/`
CPython introspection and manipulation utilities.

See there for:
- `frame.py` - Stack frame inspection
- `function.py` - Function introspection and modification
- `code.py` - Code object manipulation
- `module.py` - Module management
- `inspect.py` - Enhanced inspection utilities
- `iters.py` - Iterator protocol helpers
- `classes/` - Class introspection

### Remote Procedure Calls

#### `warpc/`
"Warp C" - Distributed Python object system enabling seamless remote execution.

See there for:
- Transparent remote object access across client/server boundary
- Message-based request/response protocol
- Resource lifecycle management
- Hook system for intercepting operations
- Support for async operations, iterators, and context managers
- Type-safe message definitions

Core components:
- `msg/` - 30+ message types for all Python operations
- `request/` - Request handling infrastructure
- `resource/` - Remote object lifecycle management
- `worlds/` - Execution context isolation
- `interceptor.py` - Operation interception framework
- `hooks.py` - Customizable behavior hooks

#### `warpc_transcode/`
Transcoding layer between Python objects and universal message format.

See there for:
- Bidirectional Python ↔ Universal message conversion
- Type-safe serialization using `msgspec`
- System ID mapping across runtimes
- Handles complex types (classes, functions, iterators, exceptions)

### Core Utilities

#### `core/`
Shared utilities used throughout the framework.

See there for:
- `log/` - Structured logging framework
- `ansi/` - Terminal color and formatting
- `collections/` - Custom collections (`bidict`, `chaindict`)
- `json.py` - Enhanced JSON handling
- `result.py` - Result/Error type system
- `futures.py` - Future utilities
- `queues.py` - Queue abstractions
- `type.py` - Type utilities
- `fmt.py` - Formatting helpers
- `hashing.py` - Hashing utilities
- `sentinels.py` - Sentinel values

#### `javascript/`
JavaScript interoperability utilities.

See there for:
- `equivalents.py` - Python/JavaScript type mappings
- `ids.py` - JavaScript-compatible ID generation

### Observability

#### `telemetry/`
OpenTelemetry integration for distributed tracing.

See there for:
- OTLP gRPC exporter configuration
- Service resource management
- Batch span processing, environment-based configuration

Environment variables
- `OTEL_EXPORTER_OTLP_ENDPOINT` - Collector endpoint
- `OTEL_SERVICE_NAME` - Service identification
- `OTEL_GENAI_CAPTURE_CONTENT` - Enable content capture

### Error Handling

#### `internal_errors/`
Hierarchical error types for internal operations.

See there for:
- `InvocationError` - Invocation lifecycle errors
- `GenerationError` - Generation and execution errors
- `ConnectionError` - Network and transport errors
- `BugError` - Internal framework bugs

All errors inherit from `AgenticaError` base class and are serializable for transmission between client and server.

### Testing

#### `testing/`
Test utilities and example code for internal development.

See there for:
- Example Python code for testing edge cases
- REPL test scenarios
- Warp transcoding test cases
- Demo scripts for various features

## Usage

This package is intended for **internal use only** within the Agentica framework. It is consumed by:
- [The Agentica Python SDK](https://github.com/symbolica-ai/agentica-python-sdk)
- [The Agentica Server](https://github.com/symbolica-ai/agentica-server)
- and it is exercised by [The Agentica TypeScript SDK](https://github.com/symbolica-ai/agentica-typescript-sdk)

External users should use the public SDK packages, not `agentica_internal` directly.

## License

This project is licensed under the [MIT License](./LICENSE).

