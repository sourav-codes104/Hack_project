import spacy

# Load English NLP model
nlp = spacy.load("en_core_web_lg")  # <-- use large model for better accuracy

def extract_places(text):
    doc = nlp(text)

    # Consider more labels that spaCy sometimes misclassifies for locations
    location_labels = ["GPE", "LOC", "FAC", "ORG", "PERSON", "NORP"]

    places = []
    for ent in doc.ents:
        if ent.label_ in location_labels:
            # Filter out common non-place "PERSON" names (like "John", "Mary", etc.)
            if ent.label_ == "PERSON" and not ent.text[0].isupper():
                continue
            places.append(ent.text)

    # Remove duplicates & strip spaces
    return list(set([p.strip() for p in places if p.strip()]))
