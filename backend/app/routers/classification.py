from fastapi import APIRouter, HTTPException
from app.core.db import get_connection
from app.models.classification import ClassificationRule, ClassificationRuleCreate, ClassificationRuleUpdate
import asyncio
import json
import uuid
from typing import List

router = APIRouter()

@router.get("/", response_model=List[ClassificationRule])
async def list_rules():
    def query():
        conn = get_connection()
        try:
            rows = conn.execute("SELECT id, name, pattern_hostname, pattern_vendor, ports, device_type, icon, priority, is_builtin, updated_at FROM classification_rules ORDER BY priority ASC, name ASC").fetchall()
            return [
                ClassificationRule(
                    id=r[0],
                    name=r[1],
                    pattern_hostname=r[2],
                    pattern_vendor=r[3],
                    ports=json.loads(r[4] or "[]"),
                    device_type=r[5],
                    icon=r[6],
                    priority=r[7],
                    is_builtin=bool(r[8]),
                    updated_at=r[9]
                ) for r in rows
            ]
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.post("/", response_model=ClassificationRule)
async def create_rule(rule: ClassificationRuleCreate):
    def insert():
        conn = get_connection()
        try:
            rule_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO classification_rules (id, name, pattern_hostname, pattern_vendor, ports, device_type, icon, priority, is_builtin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [rule_id, rule.name, rule.pattern_hostname, rule.pattern_vendor, json.dumps(rule.ports), rule.device_type, rule.icon, rule.priority, False]
            )
            from app.core.db import commit
            commit()
            row = conn.execute("SELECT id, name, pattern_hostname, pattern_vendor, ports, device_type, icon, priority, is_builtin, updated_at FROM classification_rules WHERE id = ?", [rule_id]).fetchone()
            return row
        finally:
            conn.close()
            
    row = await asyncio.to_thread(insert)
    return ClassificationRule(
        id=row[0], name=row[1], pattern_hostname=row[2], pattern_vendor=row[3],
        ports=json.loads(row[4] or "[]"), device_type=row[5], icon=row[6],
        priority=row[7], is_builtin=bool(row[8]), updated_at=row[9]
    )

@router.put("/{rule_id}", response_model=ClassificationRule)
async def update_rule(rule_id: str, payload: ClassificationRuleUpdate):
    def update():
        conn = get_connection()
        try:
            # Check if exists and not builtin
            existing = conn.execute("SELECT is_builtin FROM classification_rules WHERE id = ?", [rule_id]).fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Rule not found")
            
            updates = []
            params = []
            for k, v in payload.dict(exclude_unset=True).items():
                if k == "ports":
                    updates.append("ports = ?")
                    params.append(json.dumps(v))
                else:
                    updates.append(f"{k} = ?")
                    params.append(v)
            
            if updates:
                updates.append("updated_at = now()")
                params.append(rule_id)
                conn.execute(f"UPDATE classification_rules SET {', '.join(updates)} WHERE id = ?", params)
                from app.core.db import commit
                commit()
            
            row = conn.execute("SELECT id, name, pattern_hostname, pattern_vendor, ports, device_type, icon, priority, is_builtin, updated_at FROM classification_rules WHERE id = ?", [rule_id]).fetchone()
            return row
        finally:
            conn.close()
            
    row = await asyncio.to_thread(update)
    return ClassificationRule(
        id=row[0], name=row[1], pattern_hostname=row[2], pattern_vendor=row[3],
        ports=json.loads(row[4] or "[]"), device_type=row[5], icon=row[6],
        priority=row[7], is_builtin=bool(row[8]), updated_at=row[9]
    )

@router.delete("/{rule_id}")
async def delete_rule(rule_id: str):
    def delete():
        conn = get_connection()
        try:
            # Check if builtin
            existing = conn.execute("SELECT is_builtin FROM classification_rules WHERE id = ?", [rule_id]).fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Rule not found")
            if existing[0]:
                raise HTTPException(status_code=403, detail="Cannot delete built-in rules")
            
            conn.execute("DELETE FROM classification_rules WHERE id = ?", [rule_id])
            from app.core.db import commit
            commit()
        finally:
            conn.close()
    await asyncio.to_thread(delete)
    return {"status": "success"}
