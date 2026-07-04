"""BERT-based semantic matching for resume and job description analysis."""
import os
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Lazy loading - only load model when first used
_model = None
_tokenizer = None
_bert_available = None  # Track if BERT is available


def _load_model():
    """Load DistilBERT model and tokenizer on first use."""
    global _model, _tokenizer, _bert_available
    
    # If we already tried and failed, don't try again
    if _bert_available is False:
        return False
    
    if _model is not None:
        return True
    
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch
        
        model_name = "distilbert-base-uncased"
        logger.info(f"Loading {model_name}...")
        
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModel.from_pretrained(model_name)
        
        # Set to evaluation mode
        _model.eval()
        
        _bert_available = True
        logger.info("BERT model loaded successfully")
        return True
    except ImportError:
        logger.warning("transformers not installed. Using fallback matching.")
        _bert_available = False
        return False
    except Exception as e:
        logger.warning(f"Failed to load BERT model: {e}. Using fallback matching.")
        _bert_available = False
        return False


def get_embedding(text: str) -> Optional[np.ndarray]:
    """Get embedding vector for a single text.
    
    Args:
        text: Input text.
        
    Returns:
        Embedding vector as numpy array, or None if failed.
    """
    if not _load_model():
        return None
    
    try:
        import torch
        
        # Tokenize
        inputs = _tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512, 
            padding=True
        )
        
        # Get embeddings
        with torch.no_grad():
            outputs = _model(**inputs)
        
        # Use [CLS] token embedding (first token)
        embedding = outputs.last_hidden_state[:, 0, :].numpy()
        
        return embedding[0]  # Remove batch dimension
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}")
        return None


def get_embeddings_batch(texts: List[str]) -> List[Optional[np.ndarray]]:
    """Get embeddings for multiple texts.
    
    Args:
        texts: List of input texts.
        
    Returns:
        List of embedding vectors.
    """
    if not _load_model():
        return [None] * len(texts)
    
    try:
        import torch
        
        # Tokenize batch
        inputs = _tokenizer(
            texts, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512, 
            padding=True
        )
        
        # Get embeddings
        with torch.no_grad():
            outputs = _model(**inputs)
        
        # Use [CLS] token embeddings
        embeddings = outputs.last_hidden_state[:, 0, :].numpy()
        
        return [emb for emb in embeddings]
    except Exception as e:
        logger.error(f"Failed to get batch embeddings: {e}")
        return [None] * len(texts)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector.
        vec2: Second vector.
        
    Returns:
        Similarity score between 0 and 1.
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def calculate_semantic_similarity(resume_text: str, jd_text: str) -> Dict:
    """Calculate semantic similarity between resume and job description.
    
    Args:
        resume_text: Resume content.
        jd_text: Job description content.
        
    Returns:
        Dictionary with similarity score and analysis.
    """
    try:
        # Get embeddings
        resume_embedding = get_embedding(resume_text)
        jd_embedding = get_embedding(jd_text)
        
        if resume_embedding is None or jd_embedding is None:
            return {"score": 50, "error": "Failed to compute embeddings"}
        
        # Calculate overall similarity
        overall_similarity = cosine_similarity(resume_embedding, jd_embedding)
        
        # Extract key sections from resume
        sections = extract_sections(resume_text)
        section_similarities = {}
        
        for section_name, section_text in sections.items():
            if section_text.strip():
                section_embedding = get_embedding(section_text)
                if section_embedding is not None:
                    section_similarities[section_name] = cosine_similarity(section_embedding, jd_embedding)
        
        # Calculate weighted score
        # Skills section has highest weight
        weights = {
            "skills": 0.35,
            "experience": 0.30,
            "summary": 0.20,
            "education": 0.15
        }
        
        weighted_score = 0
        total_weight = 0
        
        for section, weight in weights.items():
            if section in section_similarities:
                weighted_score += section_similarities[section] * weight
                total_weight += weight
        
        if total_weight > 0:
            final_score = weighted_score / total_weight
        else:
            final_score = overall_similarity
        
        # Convert to 0-100 scale
        score = int(final_score * 100)
        
        return {
            "score": min(100, max(0, score)),
            "overall_similarity": overall_similarity,
            "section_similarities": section_similarities,
            "analysis": generate_analysis(final_score, section_similarities)
        }
    except Exception as e:
        logger.error(f"Semantic similarity calculation failed: {e}")
        return {"score": 50, "error": str(e)}


def extract_sections(text: str) -> Dict[str, str]:
    """Extract sections from resume text.
    
    Args:
        text: Resume text.
        
    Returns:
        Dictionary with section names and content.
    """
    sections = {
        "summary": "",
        "experience": "",
        "skills": "",
        "education": ""
    }
    
    lines = text.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Detect section headers
        if any(kw in line_lower for kw in ['summary', 'objective', 'profile', '概述', '目标']):
            current_section = 'summary'
            section_content = []
        elif any(kw in line_lower for kw in ['experience', 'work', 'employment', '工作', '经历']):
            current_section = 'experience'
            section_content = []
        elif any(kw in line_lower for kw in ['skills', 'competencies', '技术', '技能']):
            current_section = 'skills'
            section_content = []
        elif any(kw in line_lower for kw in ['education', '学历', '学位']):
            current_section = 'education'
            section_content = []
        elif current_section and line.strip():
            section_content.append(line)
    
    # Save last section
    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content)
    
    return sections


def generate_analysis(score: float, section_similarities: Dict) -> str:
    """Generate human-readable analysis of semantic match.
    
    Args:
        score: Overall similarity score (0-1).
        section_similarities: Similarity scores by section.
        
    Returns:
        Analysis text.
    """
    if score >= 0.8:
        return "Excellent match - Your resume strongly aligns with this job description"
    elif score >= 0.6:
        return "Good match - Your resume covers most key requirements"
    elif score >= 0.4:
        return "Moderate match - Consider tailoring your resume more specifically"
    else:
        return "Weak match - Significant gaps between your resume and job requirements"
