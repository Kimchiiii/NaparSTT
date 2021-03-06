from flask import Flask, request, url_for, redirect, render_template
from flask_googletrans import translator

from google_trans_new import google_translator
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import speech_recognition as sr


import os
import re
import math
import array
import string
import operator

#Natural Language Processing Libraries
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist


#------------Flask Application---------------#

app = Flask(__name__)



@app.route("/", methods=["GET", "POST"])
def index():
    transcript = ""
    if request.method == "POST":
        print("FORM DATA RECEIVED")

        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            recognizer = sr.Recognizer()
            audioFile = sr.AudioFile(file)
            with audioFile as source:
                data = recognizer.record(source)
            transcript = recognizer.recognize_google(data, key=None)

    return render_template('index.html', transcript=transcript)



@app.route("/translate")
def trans():
    return render_template("translate.html")


@app.route("/translate", methods=['POST'])
def translate():
    text = request.form['input_text']
    lang = "th"
    t = google_translator(timeout=5) 
    translated= t.translate(text.strip(), lang)

    print (translated)   
    return render_template("translate.html",output_translate = translated,original_text = text)



@app.route("/sum")
def sum():
    return render_template("sum.html")

@app.route('/sum', methods=['POST'])
def original_text_form():
    text = request.form['input_text']
    nltk.download('averaged_perceptron_tagger')
    Stopwords = set(stopwords.words('english'))
    wordlemmatizer = WordNetLemmatizer()


    def lemmatize_words(words):
        lemmatized_words = []
        for word in words:
            lemmatized_words.append(wordlemmatizer.lemmatize(word))
        return lemmatized_words
        
    def stem_words(words):
        stemmed_words = []
        for word in words:
            stemmed_words.append(stemmer.stem(word))
        return stemmed_words

    def remove_special_characters(text):
        regex = r'[^a-zA-Z0-9\s]'
        text = re.sub(regex,'',text)
        return text
        
    ##Step-3 Calculating the frequency of each word in the document

    def freq(words):
        words = [word.lower() for word in words]
        dict_freq = {}
        words_unique = []
        for word in words:
            if word not in words_unique:
                words_unique.append(word)
        for word in words_unique:
            dict_freq[word] = words.count(word)
        return dict_freq

    ##1.POS tagging function


    def pos_tagging(text):
        pos_tag = nltk.pos_tag(text.split())
        pos_tagged_noun_verb = []
        for word,tag in pos_tag:
            if tag == "NN" or tag == "NNP" or tag == "NNS" or tag == "VB" or tag == "VBD" or tag == "VBG" or tag == "VBN" or tag == "VBP" or tag == "VBZ":
                pos_tagged_noun_verb.append(word)
        return pos_tagged_noun_verb

    ##3. tf score function


    def tf_score(word,sentence):
        freq_sum = 0
        word_frequency_in_sentence = 0
        len_sentence = len(sentence)
        for word_in_sentence in sentence.split():
            if word == word_in_sentence:
                word_frequency_in_sentence = word_frequency_in_sentence + 1
        tf =  word_frequency_in_sentence/ len_sentence
        return tf
            
    ##4. idf score function

    def idf_score(no_of_sentences,word,sentences):
        no_of_sentence_containing_word = 0
        for sentence in sentences:
            sentence = remove_special_characters(str(sentence))
            sentence = re.sub(r'\d+', '', sentence)
            sentence = sentence.split()
            sentence = [word for word in sentence if word.lower() not in Stopwords and len(word)>1]
            sentence = [word.lower() for word in sentence]
            sentence = [wordlemmatizer.lemmatize(word) for word in sentence]
            if word in sentence:
                no_of_sentence_containing_word = no_of_sentence_containing_word + 1
        idf = math.log10(no_of_sentences/no_of_sentence_containing_word)
        return idf

    ##5. tfidf score function

    def tf_idf_score(tf,idf):
        return tf*idf



    ##2. Word tfidf function

    def word_tfidf(dict_freq,word,sentences,sentence):
        word_tfidf = []
        tf = tf_score(word,sentence)
        idf = idf_score(len(sentences),word,sentences)
        tf_idf = tf_idf_score(tf,idf)
        return tf_idf

    ##Step-4 Calculating sentence score

    def sentence_importance(sentence,dict_freq,sentences):
        sentence_score = 0
        sentence = remove_special_characters(str(sentence)) 
        sentence = re.sub(r'\d+', '', sentence)
        pos_tagged_sentence = [] 
        no_of_sentences = len(sentences)
        pos_tagged_sentence = pos_tagging(sentence)
        for word in pos_tagged_sentence:
            if word.lower() not in Stopwords and word not in Stopwords and len(word)>1: 
                    word = word.lower()
                    word = wordlemmatizer.lemmatize(word)
                    sentence_score = sentence_score + word_tfidf(dict_freq,word,sentences,sentence)
        return sentence_score


    tokenized_sentence = sent_tokenize(text)
    text = remove_special_characters(str(text))
    text = re.sub(r'\d+', '', text)
    tokenized_words_with_stopwords = word_tokenize(text)
   
    tokenized_words = [word for word in tokenized_words_with_stopwords if len(word) > 1]
    tokenized_words = [word.lower() for word in tokenized_words]
    tokenized_words = lemmatize_words(tokenized_words)
    word_freq = freq(tokenized_words)


    no_of_sentences = int((50 * len(tokenized_sentence))/100)

 
    c = 1
    sentence_with_importance = {}


    ##Step 5 Finding most important sentences

    for sent in tokenized_sentence:
        sentenceimp = sentence_importance(sent,word_freq,tokenized_sentence)
        sentence_with_importance[c] = sentenceimp
        c = c+1
    sentence_with_importance = sorted(sentence_with_importance.items(), key=operator.itemgetter(1),reverse=True)
    cnt = 0
    summary = []
    sentence_no = []
    for word_prob in sentence_with_importance:
        if cnt < no_of_sentences:
            sentence_no.append(word_prob[0])
            cnt = cnt+1
        else:
            break
    sentence_no.sort()
    cnt = 1
    for sentence in tokenized_sentence:
        if cnt in sentence_no:
            summary.append(sentence)
        cnt = cnt+1
    summary = " ".join(summary)

    print(summary)
    return render_template("sum.html",  original_text = text, 
                                        output_summary = summary)
    

if __name__ == "__main__":
    app.run(debug=True)
