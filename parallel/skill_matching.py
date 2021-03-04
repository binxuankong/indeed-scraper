import re
import nltk
from nltk import ngrams
from difflib import get_close_matches as gcm

# Match multiple of same skills into one
skill_dict = {
    'AB testing': 'AB Testing',
    'AI': 'Artificial Intelligence',
    'Angular': 'AngularJS',
    'Autoencoders': 'Autoencoder',
    'CNN': 'Convolutional Neural Network',
    'Convolutional Neural Networks': 'Convolutional Neural Network',
    'CNNs': 'Convolutional Neural Network',
    'Github': 'GitHub',
    'Gitlab': 'GitLab',
    'Go': 'Golang',
    'JS': 'JavaScript',
    'Javascript': 'JavaScript',
    'ML': 'Machine Learning',
    'Matlab': 'MATLAB',
    'MS Office': 'Microsoft Office',
    'NLP': 'Natural Language Processing',
    'Neural Networks': 'Neural Network',
    'Nodejs': 'NodeJS',
    'Php': 'PHP',
    'Power BI': 'PowerBI',
    'Pyspark': 'PySpark',
    'Pytorch': 'PyTorch',
    'RESTful': 'REST',
    'RNN': 'Recurrent Neural Network',
    'Recurrent Neural Networks': 'Recurrent Neural Network',
    'RNNs': 'Recurrent Neural Network',
    'Scikitlearn': 'Scikit-learn',
    'Tensorflow': 'TensorFlow',
    'Unix': 'UNIX',
    'Variational Autoencoders': 'Variational Autoencoder'
}

# For skill extraction algorithm
SKILLS = ['APACHE', 'C++', 'Financial Statements', 'MongoDB', 'R', 'Python', 'Java', 'Excel', 'Tableau', 'Statistics',
          'Natural Language Processing (NLP)', 'Unsupervised Machine Learning', 'Structured Query Language (SQL)',
          'Computer Vision', 'Supervised Machine Learning', 'Matlab', 'Extract Transform Load (ETL)', 'Deep Learning',
          'Dashboard', 'NOSQL', 'SPARK', 'Artificial Intelligence (AI)', 'Time Series Analysis', 'Power BI',
          'Regressions', 'Reinforcement', 'Graph Theory', 'Database Management System (DBMS)', 'Hadoop',
          'Cloud Technologies', 'Data Cleansing', 'Data Preparation', 'Github', 'JavaScript', 'Presentation',
          'AB Testing', 'Visualizations']
SKILL_DICT = {'MongoDB': 'Mongo DB', 'R': 'R programming', 'Python': 'Python Programming',
              'Natural Language Processing (NLP)': 'NLP', 'Structured Query Language (SQL)': 'SQL', 
              'Extract Transform Load (ETL)': 'ETL', 'Dashboard': 'Dashboards', 'Artificial Intelligence (AI)': 'AI',
              'Database Management System (DBMS)': 'DBMS', 'Data Cleansing': 'Data Cleansing / Preparation',
              'Data Preparation': 'Data Cleansing / Preparation', 'Presentation': 'Presentation Skill'}

def extract_skills(info, threshold=0.9):
    words, unigrams, bigrams, trigrams = clean_info(info)
    results = []
    for skill in SKILLS:
        s = skill
        if '(' in s:
            abb = s[s.find("(")+1:s.find(")")]
            if abb in words:
                results.append(skill)
                continue
            s = re.sub(r"[\(].*?[\)]", "", s)
        s = s.lower()
        s2 = s.split()
        if len(s2) > 1:
            if s in info.lower():
                results.append(skill)
                continue
        if len(s2) == 1:
            if len(gcm(s, unigrams, cutoff=threshold)) > 0:
                results.append(skill)
        elif len(s2) == 2:
            if len(gcm(s, bigrams, cutoff=threshold)) > 0:
                results.append(skill)
        elif len(s2) == 3:
            if len(gcm(s, trigrams, cutoff=threshold)) > 0:
                results.append(skill)
        else:
            if len(gcm(s, trigrams, cutoff=threshold)) > 0:
                results.append(skill)
    results = [SKILL_DICT[s] if s in SKILL_DICT.keys() else s for s in results]
    return list(set(results))

def clean_info(info):
    # Remove ordered list with alphabets: a), b), c),...
    words = re.sub(r'[\s\t\n|.|\(]+[a-zA-Z\s*][.|\)]+', ' ', info)
    # Remove non-ASCII characters
    words = re.sub(r'[^\x00-\x7F]+', ' ', words)
    # Remove punctuations
    words = re.sub('[\n|,|.|:|;|\-|/|\(|\)|\[|\]]', ' ', words)
    # words = nltk.word_tokenize(info)
    # unigrams = nltk.word_tokenize(info.lower())
    unigrams = [word.strip() for word in words.lower().split()]
    bigrams = [' '.join(g) for g in ngrams(unigrams, 2)]
    trigrams = [' '.join(g) for g in ngrams(unigrams, 3)]
    return words.split(), unigrams, bigrams, trigrams

def find_whole_word(search_string, input_string):
    raw_search_string = r"\b" + search_string + r"\b"
    match_output = re.search(raw_search_string, input_string)
    no_match_was_found = ( match_output is None )
    if no_match_was_found:
        return False
    else:
        return True
