# Installation steps and first run:
1. Download everything to a dedicated folder
2. Convert the dedicated folder into VENV and activate it
3. Run `pip install requirements.txt`
4. Navigate to this folder in the terminal
5. Run app via `uvicorn src.main:app --reload`

# Usage
1. Feed app with:
```
curl -X POST http://localhost:8000/ingestions/ \
-H "Content-Type: application/json" \
-d '{"file_path": "input_docs/documents_1.jsonl"}'
```
add more files via changing the body.\
2. Get all documents: `curl http://localhost:8000/documents`\
3. Specific document: `curl http://localhost:8000/documents/312` where 312 is an ID.\
4. Use the following parameters to filter `start_date, end_date, organization, tag, status, search`.\
5. `cited` is a special parameter that will sort in descending order by citation count.

# Additional information
1. The sample logs are provided in `ingestion_logs.txt`
2. The logs for app will be shown in terminal, plus saved to txt file when app is closed.
3. `/stats/` will give total documents, documents with authors and published documents amount.

# Assumptions and approaches
1. Duplicates are traced by `title + author`.
2. `search` parameters looks for `title, author` only.
3. `start_date, end_date` works best with `yyyy-MM-dd` format.
4. Only some columns were considered for data normalization: `author, open_access, peer_reviewed, citation_count, relevance_score, status`.
5. Having more time, I would create dedicated data parser app, that would stringify all data.
