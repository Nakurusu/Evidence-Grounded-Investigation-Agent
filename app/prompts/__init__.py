"""Versioned Prompt Contracts

Each prompt in this package is a VERSIONED CONTRACT between the
deterministic investigation engine and the generative LLM layer.

== What is a prompt contract? ==

A prompt contract defines:
1.  VERSION — a semver string (e.g., "1.0.0") that uniquely identifies this
    prompt's structure.  Changes to the prompt's instructions, input format,
    or expected output format MUST bump the version.
2.  INPUT — the structured data the prompt expects.  Always a Pydantic
    schema produced by the deterministic pipeline (never raw dataframes or
    unstructured text).
3.  OUTPUT — the structured output the LLM is expected to produce.  Defined
    as a Pydantic schema (Narrative for investigation narratives).
4.  TRACEABILITY RULES — constraints that generated content must honour
    (e.g., "every claim must reference source evidence").

== Why versioned contracts? ==

- REPRODUCIBILITY:  Given the same report and the same prompt version,
  regenerating should produce a structurally identical output (content may
  vary with non-deterministic models, but format is fixed).
- AUDITABILITY:  Every AIInvestigationReport records which prompt version
  produced it.  If a prompt is improved, old reports can be identified and
  optionally regenerated.
- TESTABILITY:  Prompt contracts can be validated independently — feed a
  known report in, check that the output conforms to the Narrative schema.
- PROVIDER AGNOSTICISM:  Anthropic, OpenAI, Gemini, and mock generators all
  consume the SAME prompt contract.  The contract does not mention a
  specific provider.

== How to add a new prompt ==

1. Create a new file in this directory.
2. Document the contract in the module docstring: version, input, output,
   and traceability expectations.
3. Expose PROMPT_VERSION, SYSTEM_PROMPT, and USER_MESSAGE_TEMPLATE as
   module-level attributes so the narrative service can consume them without
   knowing about the prompt's internals.

== How to change an existing prompt ==

1. Bump PROMPT_VERSION following semver:
   - MAJOR: input or output schema changed (breaking)
   - MINOR: new instructions or sections added (backward-compatible)
   - PATCH: wording improvements, no structural change
2. Update the module docstring to reflect the changes.
3. Consider whether old reports need regeneration.
"""

PROMPT_VERSION = "1.0.0"
"""Global prompt contract version.

Individual prompt modules MAY override this with their own version if they
evolve independently.  By default, all prompts in this package share the
same version.
"""
