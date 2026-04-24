
import nltk
import spacy
import re
# essential entity models downloads
nltk.downloader.download('maxent_ne_chunker')
nltk.downloader.download('words')
nltk.downloader.download('treebank')
nltk.downloader.download('maxent_treebank_pos_tagger')
nltk.downloader.download('punkt')
nltk.download('averaged_perceptron_tagger')

import re
import locationtagger

def extract_location(address_text):

    try:
        list_of_states = ["Andhra Pradesh","Arunachal Pradesh ","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana","Himachal Pradesh","Jammu and Kashmir","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal","Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli","Daman and Diu","Lakshadweep","National Capital Territory of Delhi","Puducherry"]

        # initializing sample text
        # address_text = "18,ambai sadan gajanan hou. society, vis0hrambag, sangli, willingdon college sangli, sangli, Maharashtra - 416415".title()
        address_text = address_text.title()
        # extracting entities.
        place_entity = locationtagger.find_locations(text = address_text)
         
        # getting all countries
        print("The countries in text : ")
        print(place_entity.countries)
         
        # getting all states
        print("The states in text : ")
        states_found = place_entity.regions
        print(place_entity.regions)
         
        # getting all cities
        print("The cities in text : ")
        cities_found = place_entity.cities
        print(place_entity.cities)

        if cities_found:
            cities_found = cities_found[0]
        if states_found:
            states_found = states_found[0]
        else:
            if len(states_found) == 0:
                for state in list_of_states:
                    state = state.lower()
                    address_text = address_text.lower()

                    if state in address_text:
                        try:
                            cities_found = address_text.split(state)[0].split()[-1].title()
                        except:
                            pass

                        states_found.append(state.title())
                
                if len(states_found) == 0:
                    states_found = ''
                else:
                    states_found = states_found[0]
            if len(cities_found) == 0:
                cities_found = ''
                
        if states_found == 0 and len(cities_found) > 1:
            cities_found = ''
            states_found = ''

        if isinstance(states_found, list):
            if len(states_found) == 0:
                states_found = ''

        if isinstance(cities_found, list):
           if len(cities_found) == 0:
               cities_found = ''
                
        if re.sub(r'[^a-zA-Z]', '', cities_found).lower() in ['state', 'district']:
            cities_found = ''
        return cities_found, states_found

    except Exception as e:
        print(f"Error in extracting location,{e}")
        return address_text


def get_pincode(address_text):
    regex = r"\b(?:\d[ ]*?){6}\b(?!@)"
    matches = re.finditer(regex, address_text, re.MULTILINE)
    result = []
    for match in matches:
        result.append(match.group().replace(" ", ""))

    if result:
        return result[len(result)-1]
    else:
        return result
