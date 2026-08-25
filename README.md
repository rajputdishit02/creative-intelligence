# Creative Intelligence Platform

Starter MVP for AI-assisted analysis and optimisation for marketing videos.

## Current MVP

- Streamlit interface
- Client/campaign information
- Campaign objective selection
- Target platform selection
- Marketing video upload
- Local video preview
- Placeholder analysis action

## Planned roadmap

1. Video metadata extraction
2. Scene and frame analysis
3. Audio extraction and transcription
4. Hook, pacing, CTA and story analysis
5. Evidence-based scoring
6. Client preference and brand memory
7. Historical campaign retrieval
8. Performance prediction
9. Manus-powered external research
10. Post-publish learning loop

## Setup

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Notes

Do not commit real API keys. Store them in `.env`.
Uploaded and processed media files are excluded from Git by default.
