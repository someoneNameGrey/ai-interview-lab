# Interview Mode vs Work Mode

Interview Mode means no AI help during the attempt: disable AI completion, clarify requirements, reason, implement and test. Preserve the original before receiving feedback. Review afterward and retry a fresh problem unaided. Mock mode enforces no hints/revisions inside this lab; outside tools still require your own discipline.

Work Mode means actively using AI for architecture brainstorming, code changes, test generation, debugging, documentation, eval drafting, threat modeling and design review. You still own the diff and evidence. A model-generated test can repeat the implementation's mistake, and a generated eval label can be wrong.

## Worked example
AI writes a retry handler and a test mocking that handler to return success. The test proves nothing about retries. Replace it with a fake transport that fails twice, assert attempt count and eventual outcome, and test a permanent error and cancellation. Inspect exception boundaries before accepting the patch.

Treat generated labels as drafts, review critical cases with domain judgment, and run the tests rather than trusting claimed output. Record accepted/rejected suggestions and why. Reimplement or debug one critical component without AI each week.

## Evidence gate
Maintain separate assisted project results and independent first attempts. The lab's guided exercises remain assisted even if you work alone; tutorial completion does not certify portfolio completion. Work Mode is a practice discipline, not a hidden app execution mode.

