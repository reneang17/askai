
        #################################################
        ### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
        #################################################
        # file to edit: notebooks/Askai App 8.ipynb

import os

import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, PretrainedConfig
import sqlite3, os, pandas as pd
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, pairwise_distances
from scipy.sparse import save_npz, load_npz
import pickle
from pathlib import Path
from src import AlbertForQuestionAnsweringMTL, Config
from src.utils_app import get_pred, get_contexts, get_scores, bold_answer
import pandas as pd
import re
import json
import sys


# check whether we are in a jupyter notebook or a script and set args accordingly
try:
    get_ipython
    example = "health_education" # default
    weights = weights
except:
    if len(sys.argv) < 2:
        raise ValueError("please provide the directory to the model weights as the first\
        argument in --args e.g. --args path/to/model/weights")
    elif len(sys.argv) < 3:
        weights = sys.argv[1]
        example = "health_education" # default
    elif len(sys.argv) == 3:
        weights = sys.argv[1]
        example = sys.argv[2]

# setting and loading configuration variables
config = Config(
    model = "albert-base-v2",
    pad_idx = 0,
    weights = weights,
    **json.load(open(f'examples/{example}/book-config.json',"r"))
)



# loading the model and tokenizer
model = AlbertForQuestionAnsweringMTL.from_pretrained(config.weights) # ensure pytroch_model.bin and config files are saved in directory
model.eval()
tok = AutoTokenizer.from_pretrained(config.model)


# determine the data type (whether csv or db)
if config.sections_file_type == "db":
    # connecting to the DB
    con = sqlite3.connect(f'examples/{example}/sections.{config.sections_file_type}')
    data = con.cursor()
elif config.sections_file_type == "csv":
    data = pd.read_csv(f'examples/{example}/sections.{config.sections_file_type}')

# load vectors and vectorizer
X = load_npz(f"examples/{example}/tfidf-vectors.npz")
vectorizer = pickle.load(open(f"examples/{example}/vectorizer.pkl","rb"))

import panel as pn
css = """ """ # use for custom css
pn.extension(safe_embed=True, raw_css=[css])

# creating the text input widget
question = pn.widgets.TextInput(name="Or enter your own question:", placeholder=f"Input a {config.book_name} related query here")

# creating the markdown answer, section panes
answer = pn.pane.Markdown("",width=600)
section = pn.pane.Markdown("",width=600)
section_spacer = pn.pane.Markdown("**Most Relevant Section:**")


# creating the dropdown options pane
dropdown = pn.widgets.Select(name="Try a Sample Question:",options=config.sample_questions)
dropdown.link(question, value="value")

def update_option(event):
    dropdown.value = dropdown.options[0]

question.param.watch(update_option, "value")

# create the button widget
button = pn.widgets.Button(name="Submit",button_type="warning")

# writing the call back function which will run when the generate_button is clicked
def click_cb(event):
    button.name, button.disabled = "Finding Answer...", True # change button to represent processing
    scores = get_scores(question.value, vectorizer, X) # get scored sections in descending order
    contexts = get_contexts(scores, data) # get the most relevant sections' raw texts
    pred, best_section = get_pred(contexts, question.value, model, tok, config.pad_idx) # get answer, most relevant text
    best_section = bold_answer(best_section, pred) # bolding the answer within the section
    section.object = best_section # update section pane's value
#     section.background="yellow"
    answer.object = pred # update answer pane's value
    button.name,  button.disabled = "Submit", False # change button back

# linking the on_click acton with the click_cb function
button.on_click(click_cb)

# compiling our app with the objects we have created thus far
app = pn.Row(pn.Column(dropdown,question,button,answer,section_spacer,section))

# Building the final app with a title, description, images etc.
title_style = {"font-family":"impact"}
style = {"font-family":""}
title = pn.pane.Markdown("# **askAi**",style=title_style)
desc = pn.pane.Markdown(f"Welcome to **TextBookQA**, a question answering demo for extracting answers from \
textbooks. This demo is based on the textbook, [*{config.book_name}*]({config.book_link}) \
(source: openbooks). Input a respective question and receive the answer and the relevant section.",style=style)
img1 = pn.pane.PNG(f"examples/{example}/cover.png",height=300,align="center")
footer = pn.pane.HTML("""<a href="https://github.com/devkosal/askai">Github""", align="center")
# Panel spacer object to center our title
h_spacer = pn.layout.HSpacer()
final_app = pn.Row(h_spacer, pn.Column( pn.Row(h_spacer,title,h_spacer) , desc, img1, footer, app), h_spacer)

# this command is needed in order to serve this app in production mode. (make sure to uncomment ofcourse)
final_app.servable()