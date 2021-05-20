# Text similarity using spaCy

This text similarity tool was created to suggest to the user how similar two news articles are. The main challenge here is to set accurate limits that separates the different categories of similarity. In the programme I made, similarity results were split into three categories; similar, some similarities and not similar. Which result appearing would be based on the similarity score output by spaCy.

The programme has 2 modes: Online & Offline. 
Online mode allows user to pull news articles online to compare whereas offline mode have the user upload the articles in either pdf, docx (Word doc) or txt files.

Another feature included is the option to either use spaCy's default large model or spaCy-BERT model.
