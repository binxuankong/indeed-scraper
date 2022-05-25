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