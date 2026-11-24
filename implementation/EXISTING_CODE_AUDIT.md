# Existing Prototype Audit (based on code shared in chat)

This is a preliminary review, not a fresh execution audit. Antigravity must verify each item against the actual repository.

## Known/likely issues
1. **Sentence splitting and joining:** tokenizing then joining words with spaces may damage punctuation, contractions, and formatting. Arbitrary splits can create fragments. Capitalizing fragments can lowercase proper nouns/acronyms.
2. **WordNet synonym replacement:** first-synset/random-lemma selection is not context-aware; can alter meaning, register, technical vocabulary, or grammar.
3. **Random idioms/personal touches:** may inject clichés, fake opinions, or unsupported personal experience. Should not be default behavior.
4. **Phrase deletion:** regex removal may delete valid context or leave awkward transitions.
5. **Paragraph restructuring:** length-only merging/splitting can disrupt argument structure and formatting.
6. **Heuristic score:** sentence variation, lexical diversity, contractions, and pronouns are not reliable authorship indicators. Reframe as descriptive metrics; remove detector probability claims.
7. **NLTK startup/network behavior:** downloading resources on initialization can make startup slow, fail offline, and create operational unpredictability. Make optional and explicit.
8. **Web UI XSS risk:** the previously shared approach interpolated processed text into `innerHTML` to create a textarea. Render safely with DOM APIs and set `.value`/text content.
9. **Input validation:** enforce server-side text length and type validation; handle empty/malformed requests.
10. **Production Flask:** do not use the development server/debug mode for deployment; add production WSGI and security configuration.
11. **Testing gap:** add tests for text preservation, API validation, errors, XSS, provider responses, and legacy behavior.
12. **Architecture coupling:** separate core text logic from CLI/UI and provider calls.

## Keep where useful
- CLI as a convenient local interface.
- Flask UI if already functional; improve it instead of rebuilding without cause.
- Basic analysis/readability metrics.
- Copy/download workflow.
- NLTK resources only where they provide real value and are optional.
