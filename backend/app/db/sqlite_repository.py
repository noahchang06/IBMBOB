import json
import uuid
import aiosqlite
from typing import Dict, Any, List
from app.db.repository import Repository
from app.config import settings

class SQLiteRepository(Repository):
    def __init__(self):
        # sqlite:///./creative_reasoning.db -> ./creative_reasoning.db
        self.db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        
    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    challenge_id TEXT,
                    graph_state_json TEXT,
                    constraint_state_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    label TEXT,
                    state_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                )
            ''')
            await db.commit()
            
    async def save_project(self, project_id: str, name: str, challenge_id: str, graph_state: Dict[str, Any], constraint_state: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO projects (id, name, challenge_id, graph_state_json, constraint_state_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    graph_state_json=excluded.graph_state_json,
                    constraint_state_json=excluded.constraint_state_json,
                    updated_at=CURRENT_TIMESTAMP
            ''', (project_id, name, challenge_id, json.dumps(graph_state), json.dumps(constraint_state)))
            await db.commit()

    async def load_project(self, project_id: str) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM projects WHERE id = ?', (project_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "name": row["name"],
                        "challenge_id": row["challenge_id"],
                        "graph_state": json.loads(row["graph_state_json"]),
                        "constraint_state": json.loads(row["constraint_state_json"])
                    }
                return None

    async def save_snapshot(self, project_id: str, label: str, state: Dict[str, Any]) -> str:
        snapshot_id = str(uuid.uuid4())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO snapshots (id, project_id, label, state_json)
                VALUES (?, ?, ?, ?)
            ''', (snapshot_id, project_id, label, json.dumps(state)))
            await db.commit()
        return snapshot_id

    async def list_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT id, project_id, label, created_at FROM snapshots WHERE project_id = ? ORDER BY created_at DESC', (project_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
