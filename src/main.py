import json

from datetime import datetime
from typing import List, Optional
from dateutil import parser

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import  or_, func
from sqlalchemy.orm import Session
from src.db import  SessionLocal, Author, Organization, Tag, Document, status_dict, IngestRequest, DocumentResponse
from src.logs import logger


# ==========================================
# 4. FASTAPI APPLICATION & DEPENDENCIES
# ==========================================
app = FastAPI(title="Document Intake Service")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def parse_date(date_str: str | None) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return parser.parse(date_str)
    except Exception:
        return None  # Handle "invalid-date" gracefully

def run_ingestion(file_path: str, db: Session):
    logger.info("=== INGESTION START ===")
    
    records_processed = 0
    errors = 0
    skipped_duplicates = 0
    skipped_invalid = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                records_processed += 1
                try:
                    data = json.loads(line)
                    
                    # Derived Processing Step 0: Skip invalid records
                    # 1. Structural Validation (Skips [] or primitive types)
                    if not isinstance(data, dict):
                        logger.warning(f"Line {records_processed} skipped: Expected JSON object/dict, got {type(data).__name__}")
                        skipped_invalid += 1
                        continue
                        
                    # 2. Content Validation (Skips {} or {"broken": true})
                    if not data: 
                        logger.warning(f"Line {records_processed} skipped: Empty JSON object.")
                        skipped_invalid += 1
                        continue
                        
                    if data.get("broken") is True:
                        logger.warning(f"Line {records_processed} skipped: Record is explicitly flagged as broken.")
                        skipped_invalid += 1
                        continue
                    # 3. Mandatory Fields Check (Skips records missing author_name or title)
                    author_name = data.get("author_name")
                    title = data.get("title")
                    if not author_name or not title:
                        logger.warning(f"Skipping record with missing mandatory fields (author_name/title): {data.get('external_id', 'N/A')}")
                        skipped_invalid += 1
                        continue
                    
                    # Derived Processing Step 1: Duplicate Detection
                    if db.query(Document).filter(Document.title == title, Document.author.has(Author.name == author_name)).first():
                        logger.warning(f"Skipping duplicate record: {data.get('external_id', 'N/A')}")
                        skipped_duplicates += 1
                        continue
                    
                    # Derived Processing Step 2: Auto-calculate word count if missing
                    body_text = data.get("body", "")
                    word_count = data.get("word_count")
                    if (not word_count or isinstance(word_count, str))and body_text:
                        word_count = len(body_text.split())

                    # Normalize Relations (Authors, Orgs, Tags)
                    author = None
                    if author_name:
                        author = db.query(Author).filter(Author.name == author_name).first()
                        if not author:
                            author = Author(name=author_name)
                            db.add(author)

                    org_name = data.get("organization_name")
                    org = None
                    if org_name:
                        org = db.query(Organization).filter(Organization.name == org_name).first()
                        if not org:
                            org = Organization(name=org_name)
                            db.add(org)

                    tag_list = data.get("tags", [])
                    tags_orm = []
                    for t_name in tag_list:
                        tag = db.query(Tag).filter(Tag.name == t_name).first()
                        if not tag:
                            tag = Tag(name=t_name)
                            db.add(tag)
                        tags_orm.append(tag)
                        
                    open_access = data.get("open_access")
                    if isinstance(open_access, str):
                        open_access = open_access.lower() == "true"
                    elif isinstance(open_access, bool):
                        pass
                    else:
                        open_access = None
                    
                    peer_reviewed = data.get("peer_reviewed")
                    if isinstance(peer_reviewed, str):
                        peer_reviewed = peer_reviewed.lower() == "true"
                    elif isinstance(peer_reviewed, bool):
                        pass
                    else:
                        peer_reviewed = None
                    
                    citation_count = data.get("citation_count")
                    if isinstance(citation_count, str):
                        try:
                            citation_count = int(citation_count)
                        except ValueError:
                            citation_count = None
                    
                    relevance_score = data.get("relevance_score")
                    if isinstance(relevance_score, str):
                        try:
                            relevance_score = float(relevance_score)
                        except ValueError:
                            relevance_score = None
                    elif relevance_score is not None and relevance_score >= 1:
                        relevance_score = None
                    # Create Document
                    doc = Document(
                        external_id=data.get("external_id"),
                        title=data.get("title"),
                        abstract=data.get("abstract"),
                        body=body_text,
                        published_at=parse_date(data.get("published_at")),
                        updated_at=parse_date(data.get("updated_at")),
                        source_name=data.get("source_name"),
                        language=data.get("language"),
                        status=status_dict[str(data.get("status")).lower()] if str(data.get("status")).lower() in status_dict else "unknown",
                        document_type=data.get("document_type"),
                        region=data.get("region"),
                        url=data.get("url"),
                        doi=data.get("doi"),
                        citation_count=citation_count,
                        relevance_score=relevance_score,
                        word_count=word_count,
                        page_count=data.get("page_count"),
                        version=data.get("version"),
                        open_access=open_access,
                        peer_reviewed=peer_reviewed,
                        author=author,
                        organization=org,
                        tags=tags_orm
                    )
                    
                    db.add(doc)
                    db.commit()

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON at line {records_processed}.")
                    errors += 1
                except Exception as e:
                    logger.error(f"Error processing record {records_processed}.")
                    db.rollback()
                    errors += 1

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    
    logger.info("=== INGESTION END ===")
    logger.info(f"Total lines read: {records_processed}")
    logger.info(f"Successfully inserted: {records_processed - errors - skipped_duplicates - skipped_invalid}")
    logger.info(f"Skipped (Duplicates): {skipped_duplicates}")
    logger.info(f"Skipped (Invalid): {skipped_invalid}")
    logger.info(f"Errors: {errors}")

# ==========================================
# 5. API ENDPOINTS
# ==========================================

@app.post("/ingestions")
def trigger_ingestion(request: IngestRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger import of the dataset."""
    background_tasks.add_task(run_ingestion, request.file_path, db)
    return {"message": "Ingestion started in the background. Check server console for logs."}

@app.get("/documents", response_model=List[DocumentResponse])
def get_documents(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    organization: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    cited: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List documents with filtering and pagination."""
    query = db.query(Document)

    if status:
        query = query.filter(Document.status == status)
    if start_date:
        query = query.filter(Document.published_at >= start_date)
    if end_date:
        query = query.filter(Document.published_at <= end_date)
    if tag:
        query = query.filter(Document.tags.any(Tag.name == tag))
    if organization:
        query = query.filter(Document.organization.has(Organization.name == organization))
    if search:
        query = query.filter(
            or_(
                Document.title.ilike(f"%{search}%"),
                Document.body.ilike(f"%{search}%")
            )
        )
    if cited:
        query = query.order_by(Document.citation_count.desc())

    return query.offset(skip).limit(limit).all()

@app.get("/documents/{doc_id}")
def get_document_details(doc_id: int, db: Session = Depends(get_db)):
    """Retrieve document details including related entities."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document": doc,
        "author": doc.author.name if doc.author else None,
        "organization": doc.organization.name if doc.organization else None,
        "tags": [t.name for t in doc.tags]
    }

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Return aggregated statistics."""
    total_docs = db.query(func.count(Document.id)).scalar()
    docs_with_authors = db.query(func.count(Document.id)).filter(Document.author_id != None).scalar()
    published_docs = db.query(func.count(Document.id)).filter(Document.status == "published").scalar()
    
    return {
        "total_documents": total_docs,
        "documents_with_authors": docs_with_authors,
        "published_docs": published_docs
    }