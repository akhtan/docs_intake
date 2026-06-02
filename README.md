# Installation steps and first run:
1. Download everything to a dedicated folder.
2. Convert the dedicated folder into VENV and activate it (MACOS, Linux and Windows might differ).
3. Run `pip install requirements.txt`.
4. Run app via `uvicorn src.main:app --host 127.0.0.1 --port 8090 --reload`.

# Usage
1. Feed the app, since it's empty in the repository, with Postman:
<img width="758" height="282" alt="image" src="https://github.com/user-attachments/assets/d61e9448-9bb6-4974-930f-109895a2719e" />

2. Or try to feed the app with the command below from the working folder:
`curl -H "Content-Type: application/json" -X POST http://localhost:8090/ingestions -d "{\"file_path\":\"input_docs/documents_1.jsonl\"}"` add more files via changing the body.

3. Get documents with chunks of 10 files by: `curl http://localhost:8090/documents`.
4. Get a specific document: `curl http://localhost:8090/documents/312` where 312 is an ID.
5. Use the following parameters to filter `start_date, end_date, organization, tag, status, search`.
6. `cited=true` is a special parameter that will sort in descending order by citation count.

# Additional information
1. The sample logs are provided in `ingestion_logs.txt`
2. The logs for app will be shown in terminal, plus saved to txt file when app is closed.
3. `/stats` will give total documents, documents with authors and published documents amount.

# Assumptions and approaches
1. Duplicates are tracked by `title + author`.
2. `search` parameter looks for `title, author` only.
3. `start_date, end_date` works best with `yyyy-MM-dd` format.
4. Only some columns were considered for data normalization: `author, open_access, peer_reviewed, citation_count, relevance_score, status`.
5. Having more time, I would create a dedicated data parser app, that would stringify all data.
