# Model refusals without the retrieval gate: eval/questions.jsonl

- Answers: `reports/answers/dev_nogate`, generated with the gate disabled for the questions the dev gate refused; every other question had the same context as in `reports/answers/dev`.
- Correct for an unanswerable question: the model refuses. Claimed answers count whether or not their quotes were valid.

| Model | Unanswerable seen | Refused by the model | Claimed an answer | Invalid output | Errors |
| --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 5 | 5 | 0 | 0 | 0 |
| `ollama:qwen3.5:4b@nothink` | 5 | 5 | 0 | 0 | 0 |
| `ollama:qwen3:4b@think` | 5 | 5 | 0 | 0 | 0 |

| Model | Question | Answerable | Outcome | Answer (start) |
| --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | `outside-pyro` | no | refused_model | The provided excerpts do not contain any information about voxel size or dissipation settings for Pyro smoke in Houdini. |
| `gemini:gemini-3.5-flash-lite` | `outside-performance` | no | refused_model | The provided OpenUSD excerpts do not contain information regarding how many gigabytes of video memory the city scene pay |
| `gemini:gemini-3.5-flash-lite` | `working-set` | yes | invalid_citation | Yes, USD supports this through the Payload arc, which acts as a "deferred reference" allowing you to unload parts of the |
| `gemini:gemini-3.5-flash-lite` | `docker-usdview` | no | refused_model | The provided excerpts do not contain any information regarding official Docker images or running usdview on a headless s |
| `gemini:gemini-3.5-flash-lite` | `sign-usdz` | no | refused_model | The provided excerpts do not contain instructions on how to digitally sign a usdz package with a certificate. |
| `gemini:gemini-3.5-flash-lite` | `nucleus-live-sync` | no | refused_model | The provided excerpts do not contain instructions on how to set up live sync of USD layers through an Omniverse Nucleus  |
| `ollama:qwen3.5:4b@nothink` | `outside-pyro` | no | refused_model | The provided excerpts do not contain information regarding voxel size or dissipation settings for Pyro smoke in Houdini. |
| `ollama:qwen3.5:4b@nothink` | `outside-performance` | no | refused_model | The provided excerpts do not contain information regarding the specific amount of gigabytes of video memory consumed by  |
| `ollama:qwen3.5:4b@nothink` | `working-set` | yes | refused_model |  |
| `ollama:qwen3.5:4b@nothink` | `docker-usdview` | no | refused_model | The provided excerpts describe how to use `usdview` command-line tools and its API, but they do not contain information  |
| `ollama:qwen3.5:4b@nothink` | `sign-usdz` | no | refused_model | The provided excerpts do not contain information regarding how to digitally sign a usdz package with a certificate for i |
| `ollama:qwen3.5:4b@nothink` | `nucleus-live-sync` | no | refused_model | The provided excerpts do not contain instructions on how to set up live sync of USD layers through an Omniverse Nucleus  |
| `ollama:qwen3:4b@think` | `outside-pyro` | no | refused_model | The provided excerpts do not contain information about Pyro smoke simulation parameters in Houdini, specifically voxel s |
| `ollama:qwen3:4b@think` | `outside-performance` | no | refused_model | The provided excerpts do not contain specific information about the video memory consumption in gigabytes for payloads o |
| `ollama:qwen3:4b@think` | `working-set` | yes | answer | Yes, you can keep most of the city set out of memory and only pay the cost for the buildings you're currently working on |
| `ollama:qwen3:4b@think` | `docker-usdview` | no | refused_model | The provided excerpts do not contain information about Docker images for usdview. None of the excerpts mention Docker, c |
| `ollama:qwen3:4b@think` | `sign-usdz` | no | refused_model | The provided excerpts do not contain information about digitally signing usdz packages with certificates for iOS verific |
| `ollama:qwen3:4b@think` | `nucleus-live-sync` | no | refused_model | The provided excerpts do not contain specific information about setting up live sync of USD layers through an Omniverse  |
