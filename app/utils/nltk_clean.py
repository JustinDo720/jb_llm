from nltk.corpus import stopwords
import string

# Utility Function to clean our text with important words only 
#
## Download the stopwords when you clean the text in the module you're importing this utility function in
# nltk.download('stopwords')
def clean_txt(text: str) -> str:   
    # Loop through each character and check if they're a punctuation 
    no_punc = [txt for txt in text if txt not in string.punctuation]
    
    # Joining back the string then splitting to avoid looping through characters
    no_punc = ''.join(no_punc)

    # We'll loop over the no_punc filter out the words that ARE stopwords 
    stop_words_set = set(stopwords.words('english'))
    no_stop_words = [wrd for wrd in no_punc.split() if wrd.lower() not in stop_words_set] 

    return ' '.join(no_stop_words)