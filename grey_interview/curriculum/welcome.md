# Welcome to the training room

Learn the controls before taking a mock interview. There is no timer penalty and no hiring verdict.

Your path: read a short guide -> study a worked example -> try two exercises -> get tutor feedback
-> revise or ask questions -> try a fresh interview question.

Start with Senior SWE diagnostic, then production Python, evals, agents, DeepSWE and enterprise
delivery. Build the projects outside the trainer and submit evidence in their review lessons.
Use DSA 1–3 alongside project work for two weekly unassisted coding sessions. Prerequisites guide
the order; refreshers and ML references remain optional. See TRAINING.md for the full schedule.

`grey learn` resumes unfinished training or selects the next required lesson, beginning with the diagnostic.
Use `grey learn --list` for the map, or `grey learn --lesson system-design` to jump to a topic.
`grey guide coding` reads a guide without an account, login, or model call.

## The controls

At an exercise, press Enter to write an answer. Finish with `.done` on its own line; `.cancel`
cancels input. For code, diagrams or a longer answer, use `file C:\path\to\answer.md`.
Use `hint` for a nudge, `explain TOPIC` for a tutor explanation, `guide` to reread the lesson,
or `pause` to stop. After feedback, use `retry`, `review QUESTION`, or Enter to continue.
You can revise from a file with `grey answer SESSION --file answer.md --revise`.

Your submitted work is saved before review. If the model fails, use `grey grade SESSION` or resume
with `grey learn SESSION`. Unsubmitted typing is not saved. List IDs with `grey sessions`.

## What an answer looks like

For code: state the contract, explain an approach, supply code, test edge cases, and discuss cost.
For design: state requirements, draw a flow, estimate capacity, then explain failures and tradeoffs.
For experience: explain your own actions, evidence and learning. Never invent experience or results.
It is fine to say "I don't know this part yet" and ask the tutor to explain it.

Guides and exercises are bundled and readable offline. Review, hints and explanations use your
configured model and account quota. Code and diagram text are reviewed, not executed or rendered.
Every tutorial attempt is guided; it does not raise your independent interview score.
Completing a tutorial means both exercises were reviewed, not that you have mastered the topic.

After the core tutorials, try `grey run --tracks coding system-design --turns 2`.
Use `grey run --mode mock` when you want an interview without hints or early feedback.
