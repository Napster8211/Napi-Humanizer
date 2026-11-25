# Napi Humanizer deployment

## Recommendation: Render Web Service

Render is the simplest fit for the current application. Napi Humanizer is a Flask/WGSI service with server-side provider calls, SSE streaming, and transient document extraction. Deploy it as a Render Web Service connected to this GitHub repository.

The repository includes `render.yaml`, so Render can use the following settings automatically:

- Build command: `pip install -r requirements.txt`
- Start command: `waitress-serve --listen=0.0.0.0:$PORT wsgi:app`
- Health check: `/api/v1/health`
- Provider key: configure `LLM_API_KEY` in the Render dashboard as a secret; never commit it.

Set `LLM_PROVIDER`, `LLM_BASE_URL`, and `LLM_MODEL` to match the chosen OpenAI-compatible provider. Keep `DEBUG=false` and `LOG_RAW_USER_TEXT=false` in production. The uploader extracts TXT, Markdown, DOCX, and PDF content in memory and does not persist the uploaded document.

## Vercel tradeoff

Vercel can run Flask through its Python runtime, but it turns the app into a serverless function and requires Vercel-specific static asset routing. Vercel's default function request-body limit is 4.5 MB, while this uploader intentionally supports files up to 8 MB. Vercel can support larger request bodies only through a separate public-beta configuration with additional plan/runtime requirements. For that reason, Vercel is not the recommended first deployment for this version.

Vercel remains a possible later option if the upload limit is reduced, uploads are moved to direct object storage, or the application is split into a frontend and API service.
