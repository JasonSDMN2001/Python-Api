import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example
import random

# Load your training data
TRAIN_DATA = [
    ("πάπυρος είναι ένα σύστημα διαχείρισης εγγράφων", {"entities": [(0, 7 , "PRODUCT")]}),
    ("παπυρος είναι ένα σύστημα διαχείρισης εγγράφων", {"entities": [(0, 7 , "PRODUCT")]}),
    ("papyros is a enterprise content management system", {"entities": [(0, 7 , "PRODUCT")]}),
    #("Metadata", {"entities": [(0, 8 , "PRODUCT")]}),
    #("μεταδεδομένα", {"entities": [(0, 12 , "PRODUCT")]}),
    ("OCR", {"entities": [(0, 3 , "PRODUCT")]}),
    ("WebDAV", {"entities": [(0, 6 , "PRODUCT")]}),
    ("germany is a country", {"entities": [(0, 7 , "GPE")]}),
    ("1-1-2024", {"entities": [(0, 8 , "GPE")]}),
    ("athens is a city", {"entities": [(0, 6 , "GPE")]}),
    ("Η Αθήνα είναι μία πόλη", {"entities": [(2, 7 , "GPE")]}),
    ("Με λένε Ιάσων", {"entities": [(8, 13 , "PERSON")]}),
    ("JSON", {"entities": [(0, 4 , "PRODUCT")]}),
    ("my name is Jason", {"entities": [(11, 16 , "PERSON")]}),
    ("ομάδες χρηστών", {"entities": [(0, 14 , "ORG")]}),
    ("google", {"entities": [(0, 6 , "ORG")]}),
    ("Modus is a company", {"entities": [(0, 5 , "GPE")]}),
    ("Υπουργείο Διοικητικής Ανασυγκρότησης", {"entities": [(0, 36 , "ORG")]}),
    ("σύστημα είναι απλά ένα οθσιαστικό", {"entities": [(0, 7 , "NOT_AN_ENTITY")]}),
    ("χρονοσφραγίδας", {"entities": [(0, 14 , "NOT_AN_ENTITY")]}),
    ("εγγράφων", {"entities": [(0, 8 , "NOT_AN_ENTITY")]}),
    ("υποδομής", {"entities": [(0, 8 , "NOT_AN_ENTITY")]}),
    ("Κανονισμό", {"entities": [(0, 9 , "NOT_AN_ENTITY")]}), 
    ("κ.α.", {"entities": [(0, 4 , "NOT_AN_ENTITY")]}),
    ("χρήστης", {"entities": [(0, 7 , "NOT_AN_ENTITY")]}),


]

# Load the pre-trained model
nlp = spacy.load("el_core_news_lg")

# Disable other pipeline components
other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]

# Convert training data to Example objects
examples = [Example.from_dict(nlp.make_doc(text), annotations) for text, annotations in TRAIN_DATA]

# Training loop
with nlp.disable_pipes(*other_pipes):
    optimizer = nlp.resume_training()
    for itn in range(100):
        random.shuffle(examples)
        losses = {}
        for batch in minibatch(examples, size=compounding(4.0, 32.0, 1.001)):
            nlp.update(
                batch,
                drop=0.5,
                losses=losses,
                sgd=optimizer
            )
        print("Losses", losses)
        if losses['ner'] < 1:
             break


nlp.to_disk("C:/Users/impoidanis/desktop/updated_model")