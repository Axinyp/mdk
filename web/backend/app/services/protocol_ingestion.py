import json
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.protocol import Protocol
from ..models.session import ProtocolSubmission

logger = logging.getLogger(__name__)


async def ingest(
    *,
    raw_content: str,
    source_type: str,
    brand: str,
    model_name: str,
    filename: str | None,
    session_id: str | None,
    submitter_id: int,
    db: AsyncSession,
) -> ProtocolSubmission:
    sub = ProtocolSubmission(
        id=str(uuid.uuid4()),
        session_id=session_id,
        submitter_id=submitter_id,
        source_type=source_type,
        raw_content=raw_content,
        filename=filename,
        brand=brand,
        model_name=model_name,
        review_status="pending_review",
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    logger.info("[PROTOCOL] 新提交 id=%s brand=%s model=%s", sub.id[:8], brand, model_name)
    return sub


async def approve(
    *,
    submission: ProtocolSubmission,
    reviewer_id: int,
    edited_content: str | None,
    db: AsyncSession,
) -> Protocol:
    content = edited_content or submission.raw_content
    brand_model = f"{submission.brand or ''} {submission.model_name or ''}".strip() or "未知设备"

    category = "custom"
    comm_type = "unknown"
    if submission.extracted_protocol:
        try:
            extracted = json.loads(submission.extracted_protocol)
            category = extracted.get("category", "custom")
            comm_type = extracted.get("comm_type", "unknown")
            if extracted.get("content"):
                content = extracted["content"]
        except (json.JSONDecodeError, AttributeError):
            pass

    proto = Protocol(
        category=category,
        brand_model=brand_model,
        comm_type=comm_type,
        filename=None,
        content=content,
    )
    db.add(proto)
    await db.flush()
    await db.refresh(proto)

    submission.review_status = "approved"
    submission.reviewer_id = reviewer_id
    submission.approved_protocol_id = proto.id
    await db.commit()
    logger.info("[PROTOCOL] 审核通过 submission=%s → protocol=%d", submission.id[:8], proto.id)
    return proto


async def reject(
    *,
    submission: ProtocolSubmission,
    reviewer_id: int,
    note: str,
    db: AsyncSession,
) -> None:
    submission.review_status = "rejected"
    submission.reviewer_id = reviewer_id
    submission.reviewer_note = note
    await db.commit()
    logger.info("[PROTOCOL] 审核拒绝 submission=%s", submission.id[:8])
