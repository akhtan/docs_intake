# ==========================================
# 2. DATABASE CONFIGURATION (SQLAlchemy)
# ==========================================
from pydantic import ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float, Table
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

DATABASE_URL = "sqlite:///./documents.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

status_dict = {
    "0": "archived",
    "1": "draft",
    "2": "published",
    "3": "unknown status 3",
    "4": "unknown status 4",
    "5": "unknown status 5",
    "published": "published",
    "draft": "draft",
    "archived": "archived",
}

# Association Table for Many-to-Many Tags
document_tags = Table(
    'document_tags', Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    abstract = Column(Text, nullable=True)
    body = Column(Text)
    published_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    source_name = Column(String, nullable=True)
    language = Column(String, nullable=True)
    status = Column(String, index=True)
    document_type = Column(String, nullable=True)
    region = Column(String, nullable=True)
    url = Column(String, nullable=True)
    doi = Column(String, nullable=True)
    citation_count = Column(Integer, nullable=True)
    relevance_score = Column(Float, nullable=True)
    word_count = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    version = Column(String, nullable=True)
    open_access = Column(Boolean, nullable=True)
    peer_reviewed = Column(Boolean, nullable=True)

    author_id = Column(Integer, ForeignKey('authors.id'), nullable=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True)

    author = relationship("Author")
    organization = relationship("Organization")
    tags = relationship("Tag", secondary=document_tags)

Base.metadata.create_all(bind=engine)

# ==========================================
# 3. PYDANTIC SCHEMAS (Validation & Output)
# ==========================================
class IngestRequest(BaseModel):
    file_path: str = Field(..., description="Path to the JSONL file on the local PC")

class DocumentResponse(BaseModel):
    id: int
    external_id: str
    title: str
    status: Optional[str]
    published_at: Optional[datetime]
    citation_count: Optional[float]
    model_config = ConfigDict(from_attributes=True)