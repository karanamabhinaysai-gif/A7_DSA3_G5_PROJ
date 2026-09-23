import re
from collections import defaultdict

STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
    "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't",
    'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}

def extract_keywords(text, top_n=10):
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    
    word_freq = defaultdict(int)
    word_degree = defaultdict(int)
    
    phrases = []
    current_phrase = []
    
    for word in words:
        if word in STOPWORDS:
            if current_phrase:
                phrases.append(current_phrase)
                current_phrase = []
        else:
            current_phrase.append(word)
            
    if current_phrase:
        phrases.append(current_phrase)
        
    for phrase in phrases:
        phrase_length = len(phrase)
        for word in phrase:
            word_freq[word] += 1
            word_degree[word] += phrase_length - 1
            
    word_scores = {}
    for word, freq in word_freq.items():
        word_degree[word] += freq
        word_scores[word] = word_degree[word] / freq
        
    sorted_words = sorted(word_scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_words[:top_n]

def extract_tfidf_keywords(corpus, top_n=10):
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(stop_words=list(STOPWORDS))
    X = vectorizer.fit_transform(corpus)
    feature_names = vectorizer.get_feature_names_out()
    
    doc_keywords = []
    for doc_idx in range(X.shape[0]):
        row = X.getrow(doc_idx).toarray()[0]
        top_indices = row.argsort()[-top_n:][::-1]
        keywords = [(feature_names[i], row[i]) for i in top_indices if row[i] > 0]
        doc_keywords.append(keywords)
    return doc_keywords
