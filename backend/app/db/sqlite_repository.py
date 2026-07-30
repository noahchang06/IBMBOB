import json
import uuid
import aiosqlite
from typing import Dict, Any, List
from app.db.repository import Repository
from app.config import settings
from app.models.challenge import PresetChallenge
from app.models.common import DomainType, DerivationLabel
from app.models.inspiration import Inspiration
from app.models.graph import GraphEdge, EdgeType

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
            await db.execute('''
                CREATE TABLE IF NOT EXISTS challenges (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    subtitle TEXT,
                    description TEXT,
                    domains_json TEXT,
                    tags_json TEXT
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS inspirations (
                    id TEXT PRIMARY KEY,
                    challenge_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    description TEXT,
                    historical_context TEXT,
                    key_principles_json TEXT,
                    transferable_lessons_json TEXT,
                    related_concepts_json TEXT,
                    design_implications_json TEXT,
                    derivation TEXT,
                    FOREIGN KEY(challenge_id) REFERENCES challenges(id)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS edges (
                    id TEXT PRIMARY KEY,
                    challenge_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    edge_type TEXT NOT NULL,
                    weight REAL NOT NULL,
                    relationship_description TEXT,
                    transferable_insight TEXT,
                    evidence_json TEXT,
                    derivation TEXT,
                    FOREIGN KEY(challenge_id) REFERENCES challenges(id)
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

    async def create_challenge(self, challenge: PresetChallenge) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO challenges (id, name, subtitle, description, domains_json, tags_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (challenge.id, challenge.name, challenge.subtitle, challenge.description, json.dumps([d.value for d in challenge.domains]), json.dumps(challenge.tags)))
            await db.commit()

    async def get_all_challenges(self) -> List[PresetChallenge]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM challenges') as cursor:
                rows = await cursor.fetchall()
                challenges = []
                for row in rows:
                    challenges.append(PresetChallenge(
                        id=row["id"],
                        name=row["name"],
                        subtitle=row["subtitle"],
                        description=row["description"],
                        domains=[DomainType(d) for d in json.loads(row["domains_json"])],
                        tags=json.loads(row["tags_json"]),
                        node_count=0  # Node count is not stored for user-created challenges
                    ))
                return challenges

    async def create_inspiration(self, challenge_id: str, inspiration: Inspiration) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO inspirations (id, challenge_id, name, domain, description, historical_context, key_principles_json, transferable_lessons_json, related_concepts_json, design_implications_json, derivation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (inspiration.id, challenge_id, inspiration.name, inspiration.domain.value, inspiration.description, inspiration.historical_context, json.dumps([p.model_dump() for p in inspiration.key_principles]), json.dumps(inspiration.transferable_lessons), json.dumps(inspiration.related_concepts), json.dumps(inspiration.design_implications), inspiration.derivation.value))
            await db.commit()

    async def get_inspirations_for_challenge(self, challenge_id: str) -> List[Inspiration]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM inspirations WHERE challenge_id = ?', (challenge_id,)) as cursor:
                rows = await cursor.fetchall()
                inspirations = []
                for row in rows:
                    inspirations.append(Inspiration(
                        id=row["id"],
                        name=row["name"],
                        domain=DomainType(row["domain"]),
                        description=row["description"],
                        historical_context=row["historical_context"],
                        key_principles=json.loads(row["key_principles_json"]),
                        transferable_lessons=json.loads(row["transferable_lessons_json"]),
                        related_concepts=json.loads(row["related_concepts_json"]),
                        design_implications=json.loads(row["design_implications_json"]),
                        derivation=DerivationLabel(row["derivation"])
                    ))
                return inspirations

    async def create_edge(self, challenge_id: str, edge: GraphEdge) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO edges (id, challenge_id, source_id, target_id, edge_type, weight, relationship_description, transferable_insight, evidence_json, derivation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (edge.id, challenge_id, edge.source_id, edge.target_id, edge.edge_type.value, edge.weight, edge.relationship_description, edge.transferable_insight, json.dumps(edge.evidence), edge.derivation.value))
            await db.commit()

    async def get_edges_for_challenge(self, challenge_id: str) -> List[GraphEdge]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM edges WHERE challenge_id = ?', (challenge_id,)) as cursor:
                rows = await cursor.fetchall()
                edges = []
                for row in rows:
                    edges.append(GraphEdge(
                        id=row["id"],
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        edge_type=EdgeType(row["edge_type"]),
                        weight=row["weight"],
                        relationship_description=row["relationship_description"],
                        transferable_insight=row["transferable_insight"],
                        evidence=json.loads(row["evidence_json"]),
                        derivation=DerivationLabel(row["derivation"])
                    ))
                return edges

    async def delete_challenge(self, challenge_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM challenges WHERE id = ?', (challenge_id,))
            await db.execute('DELETE FROM inspirations WHERE challenge_id = ?', (challenge_id,))
            await db.execute('DELETE FROM edges WHERE challenge_id = ?', (challenge_id,))
            await db.commit()
