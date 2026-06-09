# Nova Response Quality Plan

Goal: improve Nova AI response potency, efficiency, evidence discipline and communication
Intent tags: communication, file_context

## Response quality contract
- Start from the user's exact goal and answer that goal before adjacent ideas.
- Separate instructions, evidence, assumptions, and final answer; do not blend quoted/context text into instructions.
- Use concrete checks, commands, file paths, or dates when the answer depends on verification.
- Do not claim success, installation, network access, tests, or file edits unless tool output or provided evidence proves it.
- Prefer short, direct answers for simple chat; use sections only when they improve scanning.
- When using retrieved/file context, cite or identify the specific context item that supports the answer.
- Match tone to the recipient and preserve the user's intent instead of over-polishing away meaning.

## Improvement actions
- **Context discipline**: higher factuality and fewer off-course replies
  Implementation: Keep a bounded context pack with labeled sections and explicit operating rules before the user prompt.
- **Response contract**: clearer, more trustworthy communication
  Implementation: Inject compact rules for evidence, assumptions, verification and concise tone into model calls.
- **Structured subtasks**: more reliable tool/project planning
  Implementation: Use JSON/schema-shaped intermediate plans for routing, extraction and repair before rendering user prose.
- **Evidence loop**: less hallucinated progress
  Implementation: Prefer observe-fix-verify loops; report only validated actions and keep dry-runs separate from live actions.
- **Retrieval before recall**: better answers on repo/current-state questions
  Implementation: Search local docs/code/activity first, then browse current primary sources only when the fact may have changed.

## Research basis
- OpenAI prompt engineering guidance: Put clear instructions before context, separate context with delimiters, prefer specific constraints, and say what to do instead of only what not to do. (https://help.openai.com/en/articles/6654000-best-practices-for-prompting)
- OpenAI reasoning best practices: Use straightforward prompts with clear end goals, delimiters, and explicit constraints; avoid forcing chain-of-thought style prompts. (https://platform.openai.com/docs/guides/reasoning-best-practices)
- OpenAI structured outputs guidance: Use structured outputs or function calling for machine-readable subtasks instead of parsing free-form prose. (https://platform.openai.com/docs/guides/structured-outputs)
- Ollama structured outputs: Local Ollama calls can use JSON/schema-style formats for reliable extraction and consistent response shapes. (https://docs.ollama.com/capabilities/structured-outputs)
- ReAct paper: Interleaving reasoning with actions helps agents update plans, handle exceptions, and gather external evidence. (https://arxiv.org/abs/2210.03629)
- Retrieval-Augmented Generation paper: Retrieval plus generation improves factual specificity and allows knowledge to be updated outside model weights. (https://arxiv.org/abs/2005.11401)

## Validation
- Context preview contains response_quality_contract.
- ToolRegistry exposes response_quality_plan.
- Slash commands render the plan without calling a model.
- Targeted tests and Nova validation pass.
