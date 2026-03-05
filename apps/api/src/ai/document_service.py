"""Service for document upload and processing for RAG."""

from __future__ import annotations

import contextlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.models import Document, DocumentChunk
from src.ai.rag.chunker import chunk_text, estimate_tokens
from src.ai.rag.documents import extract_text
from src.ai.rag.embeddings import EmbeddingService
from src.core.config import settings
from src.core.exceptions import NotFoundError, ValidationError
from src.core.storage import s3_client


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()

    async def upload_document(
        self,
        template_id: uuid.UUID,
        filename: str,
        content_type: str,
        file_bytes: bytes,
        user_id: uuid.UUID,
    ) -> Document:
        """Upload a document to MinIO and create a database record."""
        # Validate file type
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if f".{ext}" not in [".pdf", ".docx", ".txt"]:
            raise ValidationError(f"Unsupported file type: .{ext}")

        # Validate file size
        max_bytes = 50 * 1024 * 1024  # 50MB
        if len(file_bytes) > max_bytes:
            raise ValidationError("File size exceeds 50MB limit")

        # Upload to MinIO
        storage_key = f"documents/{template_id}/{uuid.uuid4()}/{filename}"
        s3_client.put_object(
            Bucket=settings.minio_bucket,
            Key=storage_key,
            Body=file_bytes,
            ContentType=content_type,
        )

        # Create database record
        doc = Document(
            template_id=template_id,
            filename=filename,
            content_type=content_type,
            file_size_bytes=len(file_bytes),
            storage_key=storage_key,
            status="pending",
            uploaded_by=user_id,
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def process_document(self, document_id: uuid.UUID) -> Document:
        """Extract text, chunk, and generate embeddings for a document."""
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundError("Document not found")

        try:
            # Update status
            doc.status = "processing"
            await self.db.flush()

            # Download file from MinIO
            response = s3_client.get_object(
                Bucket=settings.minio_bucket, Key=doc.storage_key
            )
            file_bytes = response["Body"].read()

            # Extract text
            text = extract_text(file_bytes, doc.filename)

            if not text.strip():
                doc.status = "failed"
                doc.error_message = "No text could be extracted from document"
                await self.db.flush()
                return doc

            # Chunk text
            chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)

            # Generate embeddings
            embeddings = self.embedding_service.embed_texts(list(chunks))

            # Store chunks
            for i, (chunk, embedding) in enumerate(
                zip(chunks, embeddings, strict=True)
            ):
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    text=chunk,
                    token_count=estimate_tokens(chunk),
                    embedding=embedding,
                )
                self.db.add(db_chunk)

            doc.status = "ready"
            doc.chunk_count = len(chunks)
            await self.db.flush()
            await self.db.refresh(doc)
            return doc

        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            await self.db.flush()
            return doc

    async def list_documents(
        self, template_id: uuid.UUID
    ) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.template_id == template_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_document(self, document_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundError("Document not found")

        # Delete from MinIO
        with contextlib.suppress(Exception):
            s3_client.delete_object(
                Bucket=settings.minio_bucket, Key=doc.storage_key
            )

        # Delete chunks (cascades) and document
        await self.db.delete(doc)
        await self.db.flush()
