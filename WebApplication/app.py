#url_for to link the html to css file
#env\Scripts\activate to activate virtual env
#need to create requirements list

from msilib.schema import MsiDigitalCertificate
from flask import*
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, url_for 
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea
from joblib import load

import re
import string
import nltk
from nltk.corpus.reader import WordListCorpusReader

app = Flask(__name__)
# add database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = "cyberbullying" 
# initialize the database
db = SQLAlchemy(app)

class Posts(db.Model):
    post_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    content = db.Column(db.Text)
    abusive_word = db.Column(db.String(50))
    classification_result = db.Column(db.String(50))
    likelihood = db.Column(db.String(50))

# WT Form class for Blog Post page
class PostForm(FlaskForm):
	user = StringField("Username", validators=[DataRequired()])
	content = StringField("Content", validators=[DataRequired()], widget=TextArea( ))
	submit = SubmitField("Create Post", validators=[DataRequired()])

# WT Form class for Index page
class ClassifyForm(FlaskForm):
    msg = StringField("Type your message here :", validators=[DataRequired()], widget=TextArea( ))
    submit = SubmitField("Classify Text", validators=[DataRequired()])

# load the pipeline object
pipeline = load("text_classification.joblib")

# function to find likelihood 
def findLikelihood(input):
    
    proba = pipeline.predict_proba([input])[:,1]
    pred = pipeline.predict([input])
    percentage_proba = proba*100
    
    return pred, percentage_proba

# function to classify message 
def classify(input):
    
    pred = pipeline.predict([input])

    return pred

# function to find abusive word 
def wordSearch(t):

    wordList = [] #list of words from corpus
    wordFound = [] #list of abusive words extracted from the sentence

    #read the corpus
    try: 
        w = WordListCorpusReader('.', ['nltk_data\\corpora\\dataset\\AbusiveWords (final).txt'])
        wordList = w.words()
    except:
        print("File is not found!") 

    #user input 
    text = " "
    text = t

    #split the sentence into individual word
    result = re.sub('['+string.punctuation+']', '', text).split() 

    for i in wordList:
        for j in result:
            if i == j:
                wordFound.append(j)

    return wordFound


@app.route('/', methods=['GET', 'POST'])
def index():

    cForm = ClassifyForm()

    #variables for functions
    msg = "None"
    classify_msg = 0
    abusiveWord_list = []
    abusive_word = ","

    
    if cForm.validate_on_submit():
        #validate form
        msg = cForm.msg.data
        
        #clear data when user use the form next time
        cForm.msg.data

        # classify the text
        classify_msg = classify(msg)

        if classify_msg == 1:
            cyberbullying = "Cyberbullying"
        else:
            cyberbullying = "Non-Cyberbullying"

        # find abusive word
        abusiveWord_list= wordSearch(msg)
        abusive_word= abusive_word.join(abusiveWord_list)

        if len(abusiveWord_list) == 0:
            abusive_word = "There is no abusive word!"

        # predict likelihood 
        pred, percentage_proba = findLikelihood(msg)

        if (pred == 1) & (percentage_proba >= 90) & (percentage_proba <= 100):
            extremely_high = "Likelihood of cyberbullying is extremely high"

            return render_template("index.html", cForm=cForm, likelihood=extremely_high, 
                                    cyberbullying=cyberbullying, abusive_word=abusive_word)
        
        elif (pred == 1) & (percentage_proba >= 70) & (percentage_proba < 90):
            very_high = "Likelihood of cyberbullying is very high"
            return render_template("index.html", cForm=cForm, likelihood=very_high, 
                                    cyberbullying=cyberbullying, abusive_word=abusive_word )
        
        elif (pred == 1) & (percentage_proba >= 50) & (percentage_proba < 70):
            high = "Likelihood of cyberbullying is high"
            return render_template("index.html", cForm=cForm, likelihood=high, 
                                    cyberbullying=cyberbullying, abusive_word=abusive_word)
        
        elif (pred == 0) & (percentage_proba >= 30) & (percentage_proba < 50):
            low = "Likelihood of cyberbullying is low"

            return render_template("index.html", cForm=cForm, likelihood=low, 
                                    cyberbullying=cyberbullying, abusive_word=abusive_word)
        
        elif (pred == 0) & (percentage_proba >= 10) & (percentage_proba < 30):
            very_low = "Likelihood of cyberbullying is very low"

            return render_template("index.html", cForm=cForm, likelihood=very_low, 
                                    cyberbullying=cyberbullying, abusive_word=abusive_word)
        
        elif (pred == 0) & (percentage_proba >= 0) & (percentage_proba < 10):
            extremely_low = "Likelihood of cyberbullying is extremely low"

            return render_template("index.html", cForm=cForm, likelihood=extremely_low, 
                                    cyberbullying=cyberbullying, abusive_word=abusive_word)
        
        else:
            error = "Cannot determine the likelihood of cyberbullying!"
            error2 = "Cannot classify results!"
            error3 = "Cannot find abusive words!"
        
            return render_template("index.html", cForm=cForm, likelihood=error,
                                    cyberbullying=error2, abusive_word=error3)
     
    else: 
        return render_template("index.html", cForm=cForm)


# statistic page
# the app route url must follow the function name
@app.route('/stats', endpoint='stats')
def stats():

    # select all cyberbullying posts from the database
    # display username and likelihood on html
    cyberbullyingPost = Posts.query.filter_by(classification_result = 'Cyberbullying').all()

    # find all distince abusive words
    words = Posts.query.filter_by(classification_result = 'Cyberbullying').distinct().all()
    

    return render_template("statistics.html", cyberbullyingPost=cyberbullyingPost, words=words)

# Blog Post Page
@app.route('/blog_post', methods=['GET', 'POST'])
def blog_post():
    
    form = PostForm()

    # variables for functions
    message = "None"
    output = "None"
    classify_message = 0
    abusiveList = []
    abusive = " "

    # create the blog posts
    if form.validate_on_submit():
		
        # retrive the content from form 
        message = form.content.data

        # functions to classify, find abusive word, find likelihood
        # classify the text
        classify_message = classify(message)

        if classify_message == 1:
            cyberbullying = "Cyberbullying"
        else:
            cyberbullying = "Non-Cyberbullying"
    

        # find the abusive word
        # find abusive word
        abusiveList= wordSearch(message)
        abusive= abusive.join(abusiveList)

        if len(abusiveList) == 0:
            abusive = "There is no abusive word!"

        # function to predict likelihood
        # predict likelihood 
        pred, percentage_proba = findLikelihood(message)

        if (pred == 1) & (percentage_proba >= 90) & (percentage_proba <= 100):
            output = "Likelihood of cyberbullying is extremely high"
        
        elif (pred == 1) & (percentage_proba >= 70) & (percentage_proba < 90):
            output = "Likelihood of cyberbullying is very high"
        
        elif (pred == 1) & (percentage_proba >= 50) & (percentage_proba < 70):
            output = "Likelihood of cyberbullying is high"
        
        elif (pred == 0) & (percentage_proba >= 30) & (percentage_proba < 50):
            output = "Likelihood of cyberbullying is low"

        
        elif (pred == 0) & (percentage_proba >= 10) & (percentage_proba < 30):
            output = "Likelihood of cyberbullying is very low"
        
        elif (pred == 0) & (percentage_proba >= 0) & (percentage_proba < 10):
            output = "Likelihood of cyberbullying is extremely low"
        
        else:
            output = "Cannot determine the likelihood of cyberbullying!"
           

        # add these elements into the model
        post = Posts(content=form.content.data, username=form.user.data,
                    classification_result=cyberbullying, abusive_word=abusive,
                    likelihood=output)
    
        # clear the form 
        form.user.data = ''
        form.content.data = ''
		
        # add post to database
        db.session.add(post)
        db.session.commit()

    # select all posts from the database
    posts = Posts.query.order_by(Posts.post_id)
    return render_template("blog.html", form=form, posts=posts)

if __name__ == "__main__":
    app.run(debug=False) #set it to true to show error, but need to set it to FALSE if need to launch in production env