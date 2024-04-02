'''from flask import Flask, request, jsonify, Response
import json
import spacy
from spacy.matcher import Matcher
from spacy.language import Language
from spacy.tokens import Span
from spacy.pipeline import EntityRuler
import re
import pika
 
with open("RabbitMQ_Settings.json", "r") as file:
    config = json.load(file)
    rabbitmq_config = config["RabbitMQ"]

class NerResult(object):
    def __init__(self, text, entity):
        self.text = text
        self.entity = entity
    def __eq__(self, other):
        return self.text == other.text and self.entity == other.entity
    def __hash__(self):
        return hash(('text', self.text, 'entity', self.entity))

class SimpleEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__
 
        
app = Flask(__name__)
 
# set production mode
app.config["DEBUG"] = True
 
# initialize nlp engine here
nlp = spacy.load("el_core_news_lg") #, enable=["ner"])
#nlp = spacy.load("/home/impoidanis/updated_model") #, enable=["ner"])
nlp_en = spacy.load("en_core_web_lg") #, enable=["ner"])
nlp_mix = spacy.load("xx_ent_wiki_sm")
 
@Language.component("match_entities_in_parentheses")
def match_entities_in_parentheses(doc):
    #matcher = Matcher(doc.vocab)
    #pattern = [{"ORTH": "("}, {"IS_ALPHA": True, "OP": "+"}, {"ORTH": ")"}]
    #matcher.add("EntityInParentheses", [pattern])
    #matches = matcher(doc)
    #for match_id, start, end in matches:
        #yield start, end, "ENTITY_IN_PARENTHESES"

    #return doc
    matches = []
    matcher = Matcher(doc.vocab)
    pattern = [{"ORTH": "("}, {"IS_ALPHA": True, "OP": "+"}, {"ORTH": ")"}]
    matcher.add("EntityInParentheses", [pattern])
    matches = matcher(doc)

    with doc.retokenize() as retokenizer:
        for match_id, start, end in matches:
            span = doc[start:end]
            if span.text.startswith("(") and span.text.endswith(")"):
                new_span = Span(doc, start, end, label="ENTITY_IN_PARENTHESES")
                retokenizer.merge(new_span)

    return doc

ruler = EntityRuler(nlp)
patterns = [
        {"label": "ORG", "pattern": "Δ.Ε.Η."},
        {"label": "PRODUCT", "pattern": "παπυρος"},
        {"label": "PRODUCT", "pattern": "papyros"},
        {"label": "PRODUCT", "pattern": [{"LOWER": "papyros"}]},
        {"label": "PRODUCT", "pattern": "OCR"},
        {"label": "PRODUCT", "pattern": "WebDAV"},
        {"label": "GPE", "pattern": "germany"},
        {"label": "GPE", "pattern": "1-1-2024"},
        {"label": "GPE", "pattern": "athens"},
        {"label": "GPE", "pattern": "Αθήνα"},
        {"label": "PERSON", "pattern": "Ιάσων"},
        {"label": "PRODUCT", "pattern": "JSON"},
        {"label": "PERSON", "pattern": "Jason"},
        {"label": "ORG", "pattern": "google"},
        {"label": "ORG", "pattern": "Modus"},
        {"label": "ORG", "pattern": "Υπουργείο Διοικητικής Ανασυγκρότησης"},
]
ruler.add_patterns(patterns)
nlp.add_pipe("entity_ruler")  
nlp.get_pipe("entity_ruler").add_patterns(patterns)

#nlp.add_pipe("match_entities_in_parentheses", after="ner")
#nlp_en.add_pipe("match_entities_in_parentheses", after="ner")

def is_greek(text):
    return bool(re.search('[\u0370-\u03FF]', text))
def is_invalid_pattern(text):
    if re.search(r'^\d{1,4}\/\d{1,4}$', text) or re.search(r'\d+(\.\d+)?,\d+(\.\d+)?',text):
        return True
    return False

@app.post("/ner")
def process_ner():
    if request.is_json:
        data = request.get_json()
        #print(data)
        ret = []
        doc = nlp(data["content"])
        #print("doc: ",doc.ents,"\n")
        entities_to_keep = []
        for ent in doc.ents:
            #ret.append(NerResult(ent.text, ent.label_))
            if ent.label_ not in ["UNWANTED_ENTITY_TYPE1", "UNWANTED_ENTITY_TYPE2"]:  # Specify unwanted types
                entities_to_keep.append(ent)
        for ent in entities_to_keep:
            if (ent.label_ in ["PERSON", "GPE", "ORG"]) and is_invalid_pattern(ent.text):
                continue
            ret.append(NerResult(ent.text, ent.label_))

        doc_en = nlp_en(data["content"])
        #print("doc_en: ",doc_en.ents,"\n")
        for ent_en in doc_en.ents:
            if not is_greek(ent_en.text) and ent_en.label_ not in ["CARDINAL", "FAC", "DATE", "NORP", "TIME"]:
                print("doc_en: ", ent_en)
                ret.append(NerResult(ent_en.text, ent_en.label_))


        #doc_mix = nlp_en(data["content"])
        #print("nlp_mix: ",doc_mix.ents)
        #for ent_mix in doc_mix.ents:
            #ret.append(NerResult(ent_mix.text, ent_mix.label_))
        unique_entities = {}
        for entity in ret:
            key = (entity.text, entity.entity)  # Create a tuple of text and entity type
            if key not in unique_entities:
                 unique_entities[key] = entity
        ret = list(unique_entities.values())
        print("ret: ", [item.text for item in ret], "\n")
#        for sent in doc.sents:
#            text = sent.text.strip()
#            if text:
#                doc2 = nlp(text)
#                for ent in doc2.ents:
#                    #print(json.dumps(ent))
#                    #print(ent.text, ent.start_char, ent.end_char, ent.label_)
#                    ret.append(NerResult(ent.text, ent.label_))
        return Response(json.dumps(list(set(ret)), cls=SimpleEncoder, ensure_ascii=False).encode('utf8'), mimetype='application/json')
    return {"error": "Request must be JSON"}, 415
app.run(host='0.0.0.0', port=5001, debug=False)'''


from flask import Flask, jsonify
import threading
import pika
import json
import spacy
from spacy.pipeline import EntityRuler
import re
import requests

app = Flask(__name__)
nlp = spacy.load("el_core_news_lg")

class NerResult(object):
    def __init__(self, text, entity):
        self.text = text
        self.entity = entity
    def __eq__(self, other):
        return self.text == other.text and self.entity == other.entity
    def __hash__(self):
        return hash(('text', self.text, 'entity', self.entity))

class SimpleEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__
    
class MetadataType:
    TEXT = 'TEXT'  # This is an example; adjust as needed for different metadata types.

class Metadata:
    def __init__(self, name, type, value, tag):
        self.name = name
        self.type = type
        self.value = value
        self.tag = tag
 
with open("RabbitMQ_Settings.json", "r") as file:
    config = json.load(file)
    rabbitmq_config = config["RabbitMQ"]

ruler = EntityRuler(nlp)
patterns = [
        {"label": "ORG", "pattern": "Δ.E.H"},
        {"label": "PRODUCT", "pattern": "παπυρος"},
        {"label": "PRODUCT", "pattern": "papyros"},
        {"label": "PRODUCT", "pattern": [{"LOWER": "papyros"}]},
        {"label": "PRODUCT", "pattern": "OCR"},
        {"label": "PRODUCT", "pattern": "WebDAV"},
        {"label": "GPE", "pattern": "germany"},
        {"label": "GPE", "pattern": "1-1-2024"},
        {"label": "GPE", "pattern": "athens"},
        {"label": "GPE", "pattern": "Αθήνα"},
        {"label": "PERSON", "pattern": "Ιάσων"},
        {"label": "PRODUCT", "pattern": "JSON"},
        {"label": "PRODUCT", "pattern": "json"},
        {"label": "PERSON", "pattern": "Jason"},
        {"label": "PERSON", "pattern": "jason"},
        {"label": "ORG", "pattern": "google"},
        {"label": "ORG", "pattern": "Modus"},
        {"label": "ORG", "pattern": "Υπουργείο Διοικητικής Ανασυγκρότησης"},
]
ruler.add_patterns(patterns)
nlp.add_pipe("entity_ruler")  
nlp.get_pipe("entity_ruler").add_patterns(patterns)

def is_greek(text):
    return bool(re.search('[\u0370-\u03FF]', text))
def is_invalid_pattern(text):
    return bool(re.search(r'^\d{1,4}\/\d{1,4}$', text) or re.search(r'\d+(\.\d+)?,\d+(\.\d+)?', text))
  

def process_content(content):
    doc = nlp(content)
    unique_entities = {}
    for ent in doc.ents:
        if not (ent.label_ in ["PERSON", "GPE", "ORG"] and is_invalid_pattern(ent.text)):
            key = (ent.text, ent.label_)
            if key not in unique_entities:  
                unique_entities[key] = {"text": ent.text, "label": ent.label_}
    1
    ner_results = []
    metadata_results = []
    for entity in unique_entities.values():
        ner_result = NerResult(entity["text"], entity["label"])
        ner_results.append(ner_result)
        metadata = Metadata(name=entity["label"], type=1, value=entity["text"], tag=entity["label"])
        metadata_results.append(metadata)
    #print(json.dumps(ner_results, cls=SimpleEncoder, ensure_ascii=False))
    print(json.dumps(metadata_results, cls=SimpleEncoder, ensure_ascii=False))
    #publish_ner_results(ner_results)
    ner_results = list(unique_entities.values())
    for i in range(0, len(ner_results), 2):
        line = ner_results[i:i+2] 
        print(", ".join([f'{item["text"]} ({item["label"]})' for item in line]))
    #publish_ner_results(ner_results)

def on_message(channel, method, properties, body):
    data = json.loads(body)
    content = data.get('content', '')
    if content:
        process_content(content)
    channel.basic_ack(delivery_tag=method.delivery_tag)

def start_rabbitmq_listener():
    credentials = pika.PlainCredentials(rabbitmq_config['Username'], rabbitmq_config['Password'])
    parameters = pika.ConnectionParameters(host=rabbitmq_config['Host'],
                                           port=rabbitmq_config['Port'],
                                           virtual_host=rabbitmq_config['VirtualHost'],
                                           credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.basic_consume(queue='metadata-ai-queue', on_message_callback=on_message, auto_ack=False)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()

def run_listener_in_background():
    listener_thread = threading.Thread(target=start_rabbitmq_listener)
    listener_thread.daemon = True
    listener_thread.start()

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "AI Service is running."})

def publish_ner_results(ner_results):
    print(ner_results)
    url = 'http://127.0.0.2:5001/target-route' 
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=ner_results, headers=headers)
    
    if response.status_code == 200:
        print("Successfully posted NER results")
    else:
        print(f"Failed to post NER results. Status code: {response.status_code}")

if __name__ == "__main__":
    run_listener_in_background()
    app.run(host='127.0.0.1', port=5001, debug=True)

