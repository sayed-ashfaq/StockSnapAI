from __future__ import annotations
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_chroma import Chroma
from utils.model_loader import ModelLoader
from logger import GLOBAL_LOGGER as log
from exceptions.custom_exception import DocumentPortalException
from config.config import settings


class ChromaManager:
    def __init__(self, index_dir: Path, model_loader: Optional[ModelLoader] = None):
        self.index_dir = Path(index_dir) or  Path("C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\Vectore_store")
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.meta_path = self.index_dir / "ingested_meta.json"
        self._meta: Dict[str, Any] = {"rows": {}}

        if self.meta_path.exists():
            try:
                self._meta = json.loads(self.meta_path.read_text(encoding="utf-8")) or {"rows": {}}
            except Exception:
                self._meta = {"rows": {}}

        self.model_loader = model_loader or ModelLoader()
        self.emb = self.model_loader.load_embedding_model()
        self.vs: Optional[Chroma] = None

    @staticmethod
    def _fingerprint(text: str, md: Dict[str, Any]) -> str:
        """Unique hash for deduplication"""
        src = md.get("source") or md.get("file_path")
        rid = md.get("row_id")
        if src is not None:
            return f"{src}::{'' if rid is None else rid}"
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _save_meta(self):
        self.meta_path.write_text(json.dumps(self._meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_or_create(self, docs: Optional[List[Document]] = None) -> Chroma:
        try:
            if (self.index_dir / "chroma.sqlite3").exists():
                log.info("Loading existing Chroma index", index_dir=str(self.index_dir))
                self.vs = Chroma(
                    persist_directory=str(self.index_dir),
                    embedding_function=self.emb,
                )
                return self.vs

            if not docs:
                raise DocumentPortalException("No existing Chroma index and no documents provided", None)

            log.info("Creating new Chroma index", index_dir=str(self.index_dir))
            self.vs = Chroma.from_documents(
                documents=docs,
                embedding=self.emb,
                persist_directory=str(self.index_dir)
            )
            self.vs.persist()
            return self.vs

        except Exception as e:
            log.error("Failed to load_or_create Chroma", error=str(e))
            raise DocumentPortalException("Chroma load/create error", e) from e

    def add_documents(self, docs: List[Document]) -> int:
        if self.vs is None:
            raise RuntimeError("Call load_or_create() before add_documents().")

        new_docs: List[Document] = []
        for d in docs:
            key = self._fingerprint(d.page_content, d.metadata or {})
            if key in self._meta["rows"]:
                continue
            self._meta["rows"][key] = True
            new_docs.append(d)

        if new_docs:
            self.vs.add_documents(new_docs)
            self.vs.persist()
            self._save_meta()

        return len(new_docs)

    def as_retriever(self, k: int = 5):
        if self.vs is None:
            raise RuntimeError("Call load_or_create() first.")
        return self.vs.as_retriever(search_type="similarity", search_kwargs={"k": k})
