import math
import re
import unicodedata
from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

from src.rag.pdf_section_chunker import PolicySection, load_policy_sections

FASTEMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_TOP_K = 3
MIN_RELEVANCE_SCORE = 0.05
TAG_BOOST_WEIGHT = 3
TITLE_BOOST_WEIGHT = 2
CHAR_NGRAM_MIN = 3
CHAR_NGRAM_MAX = 4
VECTOR_EPSILON = 1e-9

PORTUGUESE_STOPWORDS = frozenset({
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "um", "uma", "uns", "umas", "para", "por", "com", "sem", "que",
    "qual", "quais", "como", "onde", "quando", "posso", "pode", "tem",
    "ter", "ser", "esta", "este", "isso", "meu", "minha", "meus",
    "minhas", "seu", "sua", "loja", "emporio", "musica",
})

DOMAIN_SYNONYM_MAP: Dict[str, str] = {
    "arrependi": "arrependimento devolucao devolver reembolso",
    "devolver": "devolucao arrependimento troca reembolso",
    "trocar": "troca devolucao defeito preferencia",
    "quebrado": "defeito garantia troca avaria",
    "defeituoso": "defeito garantia troca",
    "parcelar": "parcelamento parcelas cartao credito",
    "dividir": "parcelamento parcelas cartao credito",
    "endereco": "localizacao rua campo grande onde fica",
    "local": "localizacao endereco rua campo grande",
    "abre": "horario funcionamento aberto expediente",
    "fecha": "horario funcionamento fechado expediente",
    "entrega": "frete prazo correios sedex pac jadlog motoboy",
    "envio": "frete entrega correios sedex pac jadlog",
    "rastreio": "rastreamento codigo correios jadlog",
    "rastrear": "rastreamento codigo correios jadlog",
    "acessorio": "acessorios cordas palhetas cabos cases pedais amplificadores escopo",
    "encordoamento": "cordas acessorios escopo",
    "cubo": "amplificadores acessorios escopo",
    "amp": "amplificadores acessorios escopo",
}


class PolicySearchResult(BaseModel):
    section: PolicySection
    score: float = Field(..., description="Similaridade de cosseno normalizada")


def normalize_text(text: str) -> str:
    nfkd_form = unicodedata.normalize("NFKD", text.lower())
    ascii_text = "".join(ch for ch in nfkd_form if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9\s]", " ", ascii_text)


def extract_features(text: str) -> List[str]:
    normalized = normalize_text(text)
    words = [w for w in normalized.split() if len(w) > 1 and w not in PORTUGUESE_STOPWORDS]
    expanded_words = list(words)
    for word in words:
        if word in DOMAIN_SYNONYM_MAP:
            expanded_words.extend(DOMAIN_SYNONYM_MAP[word].split())
    char_ngrams = _extract_char_ngrams(expanded_words)
    return expanded_words + char_ngrams


def _extract_char_ngrams(words: List[str]) -> List[str]:
    ngrams: List[str] = []
    for word in words:
        if len(word) < CHAR_NGRAM_MIN:
            continue
        for n_size in range(CHAR_NGRAM_MIN, CHAR_NGRAM_MAX + 1):
            for idx in range(len(word) - n_size + 1):
                ngrams.append(f"#{word[idx:idx + n_size]}")
    return ngrams


class PolicyRetriever:
    """Recuperador vetorial de políticas com suporte a FastEmbed+FAISS e fallback híbrido NumPy."""

    def __init__(self, sections: Optional[List[PolicySection]] = None) -> None:
        self.sections = sections or load_policy_sections()
        self._vocabulary: Dict[str, int] = {}
        self._idf_weights: np.ndarray = np.array([])
        self._doc_matrix: np.ndarray = np.array([])
        self._faiss_index = None
        self._embedder = None
        self._initialize_index()

    def _initialize_index(self) -> None:
        if self._try_initialize_fastembed_faiss():
            return
        self._build_numpy_tfidf_index()

    def _try_initialize_fastembed_faiss(self) -> bool:
        try:
            import faiss
            from fastembed import TextEmbedding

            self._embedder = TextEmbedding(model_name=FASTEMBED_MODEL_NAME)
            corpus = [self._build_weighted_document_text(s) for s in self.sections]
            embeddings = np.array(list(self._embedder.embed(corpus)), dtype="float32")
            faiss.normalize_L2(embeddings)
            self._faiss_index = faiss.IndexFlatIP(embeddings.shape[1])
            self._faiss_index.add(embeddings)
            return True
        except Exception:
            # Fallback determinístico quando fastembed/faiss não estão presentes ou sem rede
            return False

    def _build_weighted_document_text(self, section: PolicySection) -> str:
        repeated_title = " ".join([section.title] * TITLE_BOOST_WEIGHT)
        repeated_tags = " ".join(section.tags * TAG_BOOST_WEIGHT)
        return f"{repeated_title} {repeated_tags} {section.content}"

    def _build_numpy_tfidf_index(self) -> None:
        tokenized_docs = [
            extract_features(self._build_weighted_document_text(s)) for s in self.sections
        ]
        self._vocabulary, self._idf_weights = self._compute_vocabulary_and_idf(tokenized_docs)
        vectors = [self._vectorize_tokens(tokens) for tokens in tokenized_docs]
        self._doc_matrix = np.vstack(vectors) if vectors else np.empty((0, 0))

    def _compute_vocabulary_and_idf(
        self, tokenized_docs: List[List[str]]
    ) -> Tuple[Dict[str, int], np.ndarray]:
        doc_count = len(tokenized_docs)
        doc_freq: Dict[str, int] = {}
        for tokens in tokenized_docs:
            for unique_token in set(tokens):
                doc_freq[unique_token] = doc_freq.get(unique_token, 0) + 1
        vocab = {term: idx for idx, term in enumerate(sorted(doc_freq.keys()))}
        idf = np.zeros(len(vocab), dtype="float32")
        for term, idx in vocab.items():
            idf[idx] = math.log((1.0 + doc_count) / (1.0 + doc_freq[term])) + 1.0
        return vocab, idf

    def _vectorize_tokens(self, tokens: List[str]) -> np.ndarray:
        vec = np.zeros(len(self._vocabulary), dtype="float32")
        for token in tokens:
            idx = self._vocabulary.get(token)
            if idx is not None:
                vec[idx] += 1.0
        vec *= self._idf_weights
        norm = float(np.linalg.norm(vec))
        return vec / (norm + VECTOR_EPSILON)

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> List[PolicySearchResult]:
        if not query or not query.strip():
            return []
        if self._faiss_index is not None and self._embedder is not None:
            return self._search_with_faiss(query, top_k)
        return self._search_with_numpy(query, top_k)

    def _search_with_faiss(self, query: str, top_k: int) -> List[PolicySearchResult]:
        import faiss

        query_vec = np.array(list(self._embedder.embed([query])), dtype="float32")
        faiss.normalize_L2(query_vec)
        scores, indices = self._faiss_index.search(query_vec, min(top_k, len(self.sections)))
        return [
            PolicySearchResult(section=self.sections[int(idx)], score=float(score))
            for score, idx in zip(scores[0], indices[0])
            if idx >= 0 and score >= MIN_RELEVANCE_SCORE
        ]

    def _search_with_numpy(self, query: str, top_k: int) -> List[PolicySearchResult]:
        query_tokens = extract_features(query)
        query_vec = self._vectorize_tokens(query_tokens)
        scores = np.dot(self._doc_matrix, query_vec)
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        return [
            PolicySearchResult(section=self.sections[int(idx)], score=float(scores[idx]))
            for idx in ranked_indices
            if scores[idx] >= MIN_RELEVANCE_SCORE
        ]


_default_retriever: Optional[PolicyRetriever] = None


def get_policy_retriever() -> PolicyRetriever:
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = PolicyRetriever()
    return _default_retriever


def search_store_policies(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """Busca regras e políticas oficiais da Empório da Música relevantes para a dúvida."""
    retriever = get_policy_retriever()
    results = retriever.search(query=query, top_k=top_k)
    if not results:
        return "Nenhuma seção específica encontrada no manual de políticas para esta consulta."
    formatted_blocks = [
        f"--- [{res.section.title}] (Página {res.section.page} | Relevância: {res.score:.2f}) ---\n{res.section.content}"
        for res in results
    ]
    return "\n\n".join(formatted_blocks)
