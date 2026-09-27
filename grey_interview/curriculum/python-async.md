# Async clients and bounded concurrency

Async code overlaps waiting; it does not make blocking work safe on the event loop. Use async clients for supported I/O, bounded threads for blocking I/O, and consider processes for CPU work. A semaphore limits concurrent operations but creating millions of waiting tasks can still exhaust memory. A bounded worker pool and queue bound both execution and pending work.

## Worked example
Ten thousand calls with a concurrency cap of 20 should not imply ten thousand open clients. Reuse a client owned by an async context manager. Apply an end-to-end deadline as well as per-attempt timeouts; retries cannot extend work forever. Cancel children and clean up resources when their parent request is cancelled.

Decide the contract before coding: preserve input order or completion order? Fail fast or return per-item errors? What happens to accepted but cancelled work? Do not swallow cancellation inside a generic retry handler.

Testing should observe peak in-flight work, cancellation propagation and cleanup, using a fake client and events instead of fragile wall-clock sleeps. Test a blocked producer and slow consumer as well as happy-path throughput.

## Evidence gate
Show bounded execution, timeout and cancellation behavior, then explain the difference between throughput and tail latency. Project milestone: DeepSWE M1 adapter and worker skeleton.

