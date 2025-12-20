import json
import networkx as nx
from collections import defaultdict
import numpy as np

# Try importing NLP libraries, handle missing deps gracefully
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from gensim.models import Word2Vec
    
    # Download necessary NLTK data
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
    except Exception as e:
        print(f"NLTK Download Warning: {e}")
        pass
    
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

class MindMapNode:
    def __init__(self, content):
        self.content = content
        self.children = []
        # Automatically generate a Google Search link for this concept
        self.link = f"https://www.google.com/search?q={content.replace(' ', '+')}+study+material"
        self.youtube_link = f"https://www.youtube.com/results?search_query={content.replace(' ', '+')}+tutorial"

def preprocess_text(text):
    sentences = sent_tokenize(text)
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    
    processed_sentences = []
    for sentence in sentences:
        words = word_tokenize(sentence.lower())
        words = [lemmatizer.lemmatize(word) for word in words if word.isalnum()]
        words = [word for word in words if word not in stop_words and len(word) > 2]
        if words:
            processed_sentences.append(words)
    
    return processed_sentences

def extract_key_concepts(processed_sentences, num_concepts=5):
    if not processed_sentences:
        return []
        
    # Create a single string for TF-IDF
    text = ' '.join([' '.join(sentence) for sentence in processed_sentences])
    
    # TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = dict(zip(feature_names, tfidf_matrix.toarray()[0]))
    
    # TextRank (Simplified Co-occurrence)
    text_rank = nx.Graph()
    for sentence in processed_sentences:
        for i, word1 in enumerate(sentence):
            for word2 in sentence[i+1:i+5]: # Window size 5
                if word1 != word2:
                    if text_rank.has_edge(word1, word2):
                        text_rank[word1][word2]['weight'] += 1
                    else:
                        text_rank.add_edge(word1, word2, weight=1)
    
    if len(text_rank.nodes) > 0:
        scores = nx.pagerank(text_rank)
    else:
        scores = {}
    
    # Combine TF-IDF and TextRank scores
    combined_scores = {word: (tfidf_scores.get(word, 0) + scores.get(word, 0)) / 2 for word in set(tfidf_scores) | set(scores)}
    
    key_concepts = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:num_concepts]
    return [concept for concept, _ in key_concepts]

def train_word2vec(processed_sentences):
    # min_count=1 ensures even rare words are kept for small texts
    model = Word2Vec(sentences=processed_sentences, vector_size=100, window=5, min_count=1, workers=4)
    return model

def find_related_terms(concept, word2vec_model, processed_sentences, num_terms=3):
    related_terms = []
    if concept in word2vec_model.wv:
        try:
            similar_words = word2vec_model.wv.most_similar(concept, topn=num_terms*3)
            for word, _ in similar_words:
                if word != concept and word not in related_terms:
                     # Simple check to prefer words that actually appear in context/sentences near the concept could be added here
                    related_terms.append(word)
                    if len(related_terms) >= num_terms:
                        break
        except KeyError:
            pass
            
    # Fallback: Frequency co-occurrence
    if len(related_terms) < num_terms:
        word_freq = defaultdict(int)
        for sentence in processed_sentences:
            if concept in sentence:
                for word in sentence:
                    if word != concept and word not in related_terms:
                        word_freq[word] += 1
        additional_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:num_terms-len(related_terms)]
        related_terms.extend([term for term, _ in additional_terms])
    
    return related_terms[:num_terms]

def build_mind_map(text, depth=2):
    if not NLP_AVAILABLE:
        return MindMapNode("Error: NLP libraries (nltk, sklearn, gensim) missing")
        
    processed_sentences = preprocess_text(text)
    if not processed_sentences:
         return MindMapNode("Insufficient Content")

    key_concepts = extract_key_concepts(processed_sentences, num_concepts=4) # Top 4 main branches
    word2vec_model = train_word2vec(processed_sentences)
    
    def create_node(concept, current_depth):
        node = MindMapNode(concept.capitalize())
        if current_depth < depth:
            related_terms = find_related_terms(concept, word2vec_model, processed_sentences, num_terms=3)
            for term in related_terms:
                unique_lower_children = [child.content.lower() for child in node.children]
                if term.lower() not in unique_lower_children:
                    node.children.append(create_node(term, current_depth + 1))
        return node

    root = MindMapNode("Course Concepts") # Generic Root
    for concept in key_concepts:
        root.children.append(create_node(concept, 0))
    
    return root

def mind_map_to_dict(node):
    return {
        "name": node.content,
        "link": getattr(node, 'link', ''),
        "youtube_link": getattr(node, 'youtube_link', ''),
        "children": [mind_map_to_dict(child) for child in node.children]
    }

def generate_mind_map_json(text, depth=2):
    """
    Generates JSON mind map using NLP (No AI API).
    """
    if not NLP_AVAILABLE:
        return {
            "name": "Installation Required", 
            "children": [{"name": "Please install: nltk scikit-learn gensim networkx"}]
        }
        
    try:
        mind_map = build_mind_map(text, depth)
        return mind_map_to_dict(mind_map)
    except Exception as e:
        print(f"NLP Gen Error: {e}")
        return {
            "name": "Generation Error",
            "children": [{"name": str(e)}]
        }
