# test_ner.py (place this in Hack_project/)
from model.ner_utils import extract_places
from model.ner_utils import nlp   # optional, for debugging

text = "When is best time to visit Indore and Lonavala?"
print("Input:", text)

places = extract_places(text)
print("Extracted places ->", places)

# DEBUG: show all ents and labels so we know what spaCy sees
doc = nlp(text)
print("All entities detected by spaCy:")
for ent in doc.ents:
    print(f"  - {ent.text} ({ent.label_})")
