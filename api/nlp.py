import spacy
import textract
spacynlp = spacy.load('xx')


def extract_text(filename):
    return textract.process(filename).decode('utf-8')

def get_entities(text):
    entities = []
    result = spacynlp(text)
    for entity in result.ents:
        if entity.label_ in ['PER', 'ORG']:
            entities.append(entity.text.strip())
    return entities