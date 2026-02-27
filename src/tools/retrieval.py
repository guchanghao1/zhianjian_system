"""
知识库检索工具
处理检索请求、优化查询向量、管理ChromaDB连接
仅保留安全文件规范集作为唯一知识来源
"""

from pathlib import Path

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.config import DEFAULT_CONFIG
from src.core.utils import FileUtils, CacheUtils
from src.core.logging import getLogger

logger = getLogger(__name__)


class KnowledgeRetriever:
    """知识库检索器类"""

    def __init__(self, config=None):
        self.config = dict(DEFAULT_CONFIG, **(config or {}))
        self._init_components()
        logger.info("知识库检索器初始化完成（仅保留安全规范集）")

    def _init_components(self):
        FileUtils.ensure_dir(self.config["persist_dir"])

        try:
            self.embeddings = OllamaEmbeddings(model=self.config["embedding_model"])
            logger.info("嵌入模型初始化成功")
        except Exception as e:
            logger.warning(f"Ollama嵌入模型初始化失败: {e}")
            self.embeddings = None

        self.vectorstores = {}
        self._init_default_collections()

    def _init_default_collections(self):
        """仅初始化安全规范集合"""
        for collection_name in ["safe"]:
            self._get_or_create_vectorstore(collection_name)

    def _get_or_create_vectorstore(self, collection_name):
        if collection_name in self.vectorstores:
            return self.vectorstores[collection_name]

        if self.embeddings:
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.config["persist_dir"],
            )
        else:
            vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=self.config["persist_dir"],
            )

        self.vectorstores[collection_name] = vectorstore
        return vectorstore

    def add_documents(self, file_path, collection_name="safe"):
        """添加文档到知识库，仅支持安全规范集合"""
        try:
            if collection_name != "safe":
                logger.warning(f"仅支持安全规范集合，忽略集合: {collection_name}")
                return {"success": False, "error": "仅支持安全规范集合"}

            docs = FileUtils.load_file(file_path)
            if not docs:
                return {
                    "success": False,
                    "error": "无法加载文档，请检查文件是否存在且格式正确",
                }

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config["chunk_size"],
                chunk_overlap=self.config["chunk_overlap"],
            )
            split_docs = text_splitter.split_documents(docs)

            vectorstore = self._get_or_create_vectorstore(collection_name)
            vectorstore.add_documents(split_docs)

            logger.info(f"成功添加 {len(split_docs)} 个文档片段到安全规范集")
            return {
                "success": True,
                "num_chunks": len(split_docs),
                "collection": collection_name,
            }
        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def retrieve(self, query, collection_name="safe", k=None):
        """从知识库检索相关文档，仅使用安全规范集合"""
        if k is None:
            k = self.config["retrieval_k"]

        cache_key = f"retrieve_{collection_name}_{k}_{hash(query)}"
        cached_result = CacheUtils.get(cache_key)
        if cached_result:
            logger.info("从缓存获取检索结果")
            return cached_result

        try:
            vectorstore = self._get_or_create_vectorstore(collection_name)

            if self.embeddings:
                results = vectorstore.similarity_search(query, k=k)
            else:
                results = []
                logger.warning("嵌入模型不可用")

            CacheUtils.set(cache_key, results)
            logger.info(f"从安全规范集检索到 {len(results)} 个相关文档")
            return results
        except Exception as e:
            logger.error(f"检索失败: {str(e)}")
            return []

    def get_collection_stats(self, collection_name="safe"):
        """获取集合统计信息，仅支持安全规范集合"""
        try:
            if collection_name != "safe":
                return {"collection": collection_name, "error": "仅支持安全规范集合"}

            vectorstore = self._get_or_create_vectorstore(collection_name)
            count = len(vectorstore.get()["ids"])
            return {"collection": collection_name, "document_count": count}
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {"collection": collection_name, "error": str(e)}

    def clear_collection(self, collection_name="safe"):
        """清空集合，仅支持安全规范集合"""
        try:
            if collection_name != "safe":
                return {"success": False, "error": "仅支持安全规范集合"}

            vectorstore = self._get_or_create_vectorstore(collection_name)
            vectorstore.delete_collection()

            if collection_name in self.vectorstores:
                del self.vectorstores[collection_name]

            self._get_or_create_vectorstore(collection_name)
            logger.info(f"已清空安全规范集合")
            return {"success": True, "collection": collection_name}
        except Exception as e:
            logger.error(f"清空集合失败: {str(e)}")
            return {"success": False, "error": str(e)}
