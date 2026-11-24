# Suggested Modular Structure

Adapt this to the existing repository. Do not force a directory migration if a smaller refactor achieves the separation.

```text
project/
  app.py or web_ui.py              # app entry point
  cli.py                           # CLI
  core/
    config.py
    schemas.py
    errors.py
    analyzer.py
    orchestrator.py
    prompt_builder.py
    validator.py
    metrics.py
  providers/
    base.py
    openai_compatible.py
    factory.py
  editing/
    modes.py
    deterministic_tools.py
  api/
    routes.py
    middleware.py
  ui/                               # templates/static if Flask
  tests/
    unit/
    integration/
    security/
    fixtures/
  docs/
  .env.example
  .gitignore
  requirements.txt
```

Keep legacy import compatibility where practical. Use type hints and small functions. Avoid circular imports. Add dependency injection so tests can mock provider calls without network access.
