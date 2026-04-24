import json
from operator import truediv
import re

from cv2 import line
from fuzzywuzzy import fuzz
import azure_ocr
import re
import statistics
import logging


#Setting the Loggers
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Reading the json data, which is obtained from the azure ocr api

#=================uncomment bellow to get simple ocr====================
found_uidai = None
def plain_ocr(lines_data):
    address = []
    address_confidence = []
    sentence_bbox = {}
    for data in lines_data:                           
        avg_confidence = avg_confidence = address_line_bbox_check(data)
        if avg_confidence > 0.90: 
            sentence_bbox[data['text']] = (data['boundingBox'],str(round(avg_confidence*100))+"%")
        else:
            pass
        #sentence_bbox[data['text']] = data['boundingBox']
        for word in data['words']:
            if word['confidence'] > 0.90:
                #print("word: ",word['text'],"=> confidence: ",word['confidence'])
                address.append(word['text'])
                address_confidence.append(word['confidence'])
    final_address = ' '.join(address)
    #print("sentence_bbox: ",sentence_bbox)
    try:
        final_address_confidence = statistics.mean(address_confidence)*100
    except Exception as e:
        logger.error("Could not calc accuracy", exc_info=True)
        final_address_confidence = 0
    #print("final_address_confidence: ",final_address_confidence)
    #print("final_address from the plain ocr")
    return final_address,final_address_confidence,sentence_bbox
    #return {'Address': final_address, "Accuracy":final_address_confidence}
# ============= simple ocr code end ===============================
def adhaar_back_check(adhaar_back_ocr_data):
    #print('adhaar_back_check called')
    for lines_idex, lines in enumerate(adhaar_back_ocr_data):
        front_address = None
        #print(lines['text'],fuzz.ratio('UNIQUE IDENTIFICATION AUTHORITY OF INDIA'.lower(),lines['text'].lower()))
        #print("word: ",lines['words'][0]['text'],fuzz.ratio('To'.lower(), lines['words'][0]['text'].lower()))
        if fuzz.ratio('To'.lower(), lines['words'][0]['text'].lower()) >= 80:
            front_address = True
            break
        else:
            front_address = False
            continue
    return front_address 

def adhaar_front_get_address(adhaar_back_ocr_data):
    #print('adhaar_front_get_address called')
    address_list = []
    address_confidence = []
    sentence_bbox = {}
    found_to = None
    found_mobile = None
    for lines_idex, lines in enumerate(adhaar_back_ocr_data):
        #print("word: ",lines['words'][0]['text'],fuzz.ratio('To'.lower(), lines['words'][0]['text'].lower()))
        #print("lines_data:",lines)
        if fuzz.ratio('To'.lower(), lines['words'][0]['text'].lower()) >= 80:
            #print("lines['words'][0]['text']: ",lines['words'][0]['text'])
            get_word_confidence_mean(new_data=lines,address_confidence=address_confidence)
            avg_address_line_confidence = address_line_bbox_check(lines)
            if avg_address_line_confidence > 0.90:
                if 'Date' not in lines['text']:
                    sentence_bbox[lines['text']] = (lines['boundingBox'],str(round(avg_address_line_confidence*100))+"%")
                else:
                    pass
            else:
                pass
            found_to = True
            for data in lines['words']:
                address_list.append(data['text'])
                #print("address_list from if: ",address_list)
        else:
            if found_to:
                #print("lines['words']")
                if 'Ref.' in lines['text'].split():
                    break
                else:
                    get_word_confidence_mean(new_data=lines,address_confidence=address_confidence)
                    avg_address_line_confidence = address_line_bbox_check(lines)
                    if avg_address_line_confidence > 0.90:
                        if 'Date' not in lines['text']:
                            sentence_bbox[lines['text']] = (lines['boundingBox'],str(round(avg_address_line_confidence*100))+"%")
                        else:
                            pass
                    else:
                        pass
                for data in lines['words']:
                    #print("data['text']:",data['text'])
                    #Pincode
                    #regex = "^[1-9]{1}[0-9]{2}\\s{0,1}[0-9]{3}$"
                    #Mobile Number
                    regex = "^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$"
                    p = re.compile(regex)
                    m = re.match(p, data['text'])

                    if m is None:
                        # get_word_confidence_mean(new_data=lines,address_confidence=address_confidence)
                        address_list.append(data['text'])
                        #print("address_list from if of else: ",address_list)
                    else:
                        found_mobile = True
                        # get_word_confidence_mean(new_data=lines,address_confidence=address_confidence)
                        address_list.append(data['text'])
                        #print("address_list from else of else: ",address_list)
                        break
                if found_mobile:
                    break       
            else:
                continue

    for elements_in_list in address_list:
        date_pattern = r'(\d{2}/\d{2}/\d{4})'
        match_date = re.match(date_pattern, elements_in_list)
        if match_date:
            #print(match_date)
            #print("match_date.group(): ",type(match_date.group()))
            if 'Date:' in address_list:
                #print("address_list: ",address_list)
                #del address_confidence[address_list.index('Date:')]
                del address_list[address_list.index('Date:')]
                del address_list[address_list.index(match_date.group())]
            else:
                #print("address_list from else: ",address_list)
                #print("address_confidence: ",address_confidence)
                #del address_confidence[address_list.index(match_date.group())]
                del address_list[address_list.index(match_date.group())]
            break
        else:
            pass 
    if 'Ref.' in address_list:
        end_point = address_list.index('Ref.')
        #address_confidence = address_confidence[:end_point]
        #print("address_confidence before final mean if of Ref: ",address_confidence)
        final_address = ' '.join(address_list[:end_point])
        address_confidence = statistics.mean(address_confidence)
        #print("address_confidence after final mean from if of Ref: ",address_confidence)

    else:
        final_address = ' '.join(address_list)
        final_address_confidence = statistics.mean(address_confidence)*100
        #print("address_list length: ",len(address_list))
        #print("address_confidence length: ",len(address_confidence))
    return final_address,address_confidence,final_address_confidence,sentence_bbox


def ocr_call(image_front:str = None,image_back:str = None):
    if image_front and image_back:
        adr_front_data = adr_front(image_front)
        adr_back_data = adr_back_get_address(image_back)
        return {'front_details':adr_front_data,'back_details':adr_back_data}
    if image_front:
        adr_front_data = adr_front(image_front)
        return {'front_details':adr_front_data,'back_details':""}
    if image_back: 
        adr_back_data = adr_back_get_address(image_back)
        return {'front_details':"",'back_details':adr_back_data}
    #return {'front_details':adr_front_data,'address':adr_back_data}

def get_word_confidence_mean(new_data,sample_json_confidence=None,key=None,address_confidence=None,text=None):
    #print("get_word_confidence_mean called: ",address_confidence)
    word_confidence = []
    
    for idx in range(0,len(new_data['text'].split())):
        if new_data['words'][idx]['text'] == new_data['text'].split()[idx] :
            #word_confidence.append(new_data['words'][idx]['confidence'])
            if key:
                word_confidence.append(new_data['words'][idx]['confidence'])
                #new_data['words'][idx]['boundingBox']
            elif new_data['words'][idx]['text'] == text:
                #print("get address confidenc text: ",text)
                #print("new_data['words'][idx]['confidence']: ",new_data['words'][idx]['confidence'])
                word_confidence.append(new_data['words'][idx]['confidence'])
                #sample_json_words_bbox[new_data['words'][idx]['text']] = new_data['words'][idx]['boundingBox']

            if text == None:
                #print("Inside the else part of the get address confidence")
                date_pattern = r'(\d{2}/\d{2}/\d{4})'
                match_date = re.match(date_pattern, new_data['words'][idx]['text'])
                if match_date or ('Date:' == new_data['words'][idx]['text']):
                    pass
                else:
                    word_confidence.append(new_data['words'][idx]['confidence'])
                    #sample_json_words_bbox[new_data['words'][idx]['text']] = new_data['words'][idx]['boundingBox']

    if sample_json_confidence:
        sample_json_confidence[key] = statistics.mean(word_confidence)
    else:
        if word_confidence:
            #print("text: ",text)
            #print("word_confidence: ",word_confidence)
            address_confidence.append(statistics.mean(word_confidence))
        else:
            pass
        #print("address_confidence from get_word_confidence_mean: ",address_confidence)
    return 

# creating the word by word bbox for the adhaar front
def get_word_bbox_with_conf(lines_data,sentence):
    #print("lines_data from get_word_bbox_with_conf",lines_data)
    found_sentence_index = None
    each_word_bbox = []
    for idx,value in enumerate(lines_data):
        #print("value['text']: ",value['text'],'sentence: ',sentence)
        if sentence in value['text']:
            found_sentence_index = idx
            for item in lines_data[found_sentence_index]['words']:
                #print(" from outside if item['text]: ",item['text'],'sentence: ',sentence)
                if len(item['text'].split(':')) > 1:
                    #print("item['text'].split(':') ",item['text'],item['text'].split(':'),sentence)
                    word = item['text'].split(':')[1]
                    #print("word: ",word)
                else:
                    word = item['text']
                if (word in sentence) and word:
                    #print("word: ",word,'sentence: ',sentence)
                    each_word_bbox.append((item['boundingBox'],str(round(item['confidence']*100))+'%'))
            # break
        else:
            continue
    #print("sentence: ",sentence)
    #print("found_sentence_index: ",found_sentence_index)
    # for item in lines_data[found_sentence_index]['words']:
    #     each_word_bbox.append((item['boundingBox'],str(round(item['confidence']*100))+'%'))
    #print("each_word_bbox: ",each_word_bbox)
    return each_word_bbox

# Function to check wheater the address line bbox should add in the final bbox or not using confidence
def address_line_bbox_check(lines_data):
    address_line_confidence = []
    #print("lines_data['words']",lines_data['words'])
    for word in lines_data['words']:
        #print("word: ",word)
        address_line_confidence.append(word['confidence'])
    avg_confidence =  statistics.median(address_line_confidence)
    #print("avg_confidence:",avg_confidence)
    return avg_confidence
        
# Function for Processing the Aadhar front side image of any format
def adr_front(image_front): # Pass the json data to the function
    json_data = azure_ocr.azure_call(image_front)
    # print("Total length of Keys: ", len(json_data['analyzeResult']['readResults'][0]['lines']), '\n')
    lines_data = json_data['analyzeResult']['readResults'][0]['lines']
    logger.info(lines_data)
    # ===================== FULL TEXT EXTRACTION ===================== #
    full_text_lines = [line['text'] for line in lines_data]
    full_text = "\n".join(full_text_lines)

    print("\n===== FULL OCR TEXT (AADHAAR FRONT) =====\n")
    print(full_text)
    print("\n========================================\n")
        #front = False
    #header_found = False
    confidence_counter = 0

    for ld in lines_data:

        if fuzz.ratio("GOVERNMENT OF INDIA", ld['text']) > 90:
            lines_data = lines_data[lines_data.index(ld):]

        conf = [var['confidence'] for var in ld['words'] if var['confidence']]
        conf_avg = sum(conf) / len(conf)

        if round(conf_avg,2) <= 0.61:
            lines_data.remove(ld)
    sample_json = {'Name':'','Year_of_birth/DOB':'','Gender':'','Adhaar_Number':'','Bounding_Box':'','Accuracy':''}
    sample_json_confidence = {"Name_confidence":'','Year_of_birth/DOB_confidence':'','Gender_confidence':'','Adhaar_Number_confidence':''}
    sentence_bbox = {}
    for new_data in lines_data:
        #print('new_data text',new_data['text'],'counter',confidence_counter)
        #print('fuzz ratio',fuzz.ratio("GOVERNMENT OF INDIA".lower(), new_data['text'].lower()))
        if fuzz.ratio("GOVERNMENT OF INDIA".lower(), new_data['text'].lower()) > 95:
            confidence_counter +=1
            #header_found =True
            #print('GOV counter', confidence_counter)
            continue

        #print('lines_data.index(new_data)',lines_data.index(new_data))
        if  lines_data.index(new_data) == 1:
            #print('new_data["text"]: ',new_data['text'])
            #print("new_data: ",new_data)
            sample_json['Name'] = new_data['text']
            #sentence_bbox[new_data['text']] = new_data['boundingBox'] 
            sentence_bbox['Name'] = get_word_bbox_with_conf(lines_data,new_data['text']) 
            get_word_confidence_mean(new_data,sample_json_confidence,'Name_confidence')
            # word_confidence = []
            # for idx in range(0,len(new_data['text'].split())):
            #     if new_data['words'][idx]['text'] == new_data['text'].split()[idx] :
            #        word_confidence.append(new_data['words'][idx]['confidence'])
            # sample_json_confidence['Name_confidence'] = statistics.mean(word_confidence)
            confidence_counter +=1
            #header_found = False
            #print('Name counter', confidence_counter)
            continue


        text_val = new_data['text']
        #print("text_val before delimiter: ",text_val,new_data)
        word_delim_idx_arr = [char_idx for char_idx, char_val in enumerate(text_val) if char_val == "/" or char_val == ":"]
        #print("word_delim_idx_arr: ",word_delim_idx_arr)

        if len(word_delim_idx_arr) > 0 :
            text_val = text_val[word_delim_idx_arr[0]+1:]
            # print("text_val: ",text_val)

        #print("New data", new_data['text'])
        #dob_value = new_data['text'].replace("/", "")
            date_pattern_1 = r'(\d{2}/\d{2}/\d{4})'
            date_pattern_2 = r'(\d{4})'
            date_pattern_3 = r'(\d{2}-\d{2}-\d{4})'
            match_date_1 = re.search(date_pattern_1, text_val) #ew_data['text']
            match_date_2 = re.search(date_pattern_2, text_val) #ew_data['text']
            match_date_3 = re.search(date_pattern_3, text_val) #ew_data['text']
            #print("match_date_1: ",match_date_1)
            #print("match_date_2: ",match_date_2)
            #print("match_date_3: ",match_date_3)
            # if sample_json["Year of birth/DOB"] == "":
            if match_date_1 or match_date_2 or match_date_3:

                if sample_json['Year_of_birth/DOB']:
                    # lines_data.remove(new_data)
                    continue
                if match_date_1:
                    #print("Matched date 1 ", match_date_1.group())
                    sample_json["Year_of_birth/DOB"] = match_date_1.group()
                    #sentence_bbox[new_data['text']] = new_data['boundingBox']
                    sentence_bbox['DOB'] = get_word_bbox_with_conf(lines_data, match_date_1.group())
                    get_word_confidence_mean(new_data,sample_json_confidence,'Year_of_birth/DOB_confidence')
                    # sample_json_confidence['Year_of_birth/DOB_confidence'] = statistics.mean(word_confidence)
                    confidence_counter +=1
                    #print(' date of birth counter', confidence_counter)

                elif match_date_2:
                    #print("Matched date 2 ", match_date_2.group())
                    sample_json["Year_of_birth/DOB"] = match_date_2.group()
                    #sentence_bbox[new_data['text']] = new_data['boundingBox']
                    sentence_bbox['DOB'] = get_word_bbox_with_conf(lines_data, match_date_2.group())
                    get_word_confidence_mean(new_data,sample_json_confidence,'Year_of_birth/DOB_confidence')
                    
                    # sample_json_confidence['Year_of_birth/DOB_confidence'] = statistics.mean(word_confidence)
                    confidence_counter +=1
                    #print('year of birth counter', confidence_counter)
                if match_date_3:
                    #print("Matched date 3 ", match_date_3.group())
                    sample_json["Year_of_birth/DOB"] = match_date_3.group()
                    #sentence_bbox[new_data['text']] = new_data['boundingBox']
                    sentence_bbox['DOB'] = get_word_bbox_with_conf(lines_data, match_date_3.group())
                    get_word_confidence_mean(new_data,sample_json_confidence,'Year_of_birth/DOB_confidence')
                    
                    # sample_json_confidence['Year_of_birth/DOB_confidence'] = statistics.mean(word_confidence)
                    confidence_counter +=1
                    #print('year of birth counter', confidence_counter)
                continue

            if sample_json["Year_of_birth/DOB"]:
                #print(sample_json["Year of birth/DOB"])
                #print('Gender: ',text_val)
                sample_json["Gender"] = text_val
                #sentence_bbox[new_data['text']] = new_data['boundingBox']
                sentence_bbox['Gender'] = get_word_bbox_with_conf(lines_data, text_val)
                get_word_confidence_mean(new_data,sample_json_confidence,'Gender_confidence')
               
                # sample_json_confidence['Gender_confidence'] = statistics.mean(word_confidence)
                confidence_counter += 1
                #print('Gender counter', confidence_counter)
                continue
        #print(sample_json["Gender"])
        if sample_json["Gender"]:
            #print(text_val)
            adhaar_array = text_val.split(' ')
            adhaar_check = [True if num.isdigit() else False for num in adhaar_array]

            if all(adhaar_check):
                sample_json["Adhaar_Number"] = ' '.join(adhaar_array)
                #sentence_bbox[new_data['text']] = new_data['boundingBox']
                sentence_bbox['Adhaar_Number'] = get_word_bbox_with_conf(lines_data, ' '.join(adhaar_array))
                get_word_confidence_mean(new_data,sample_json_confidence,'Adhaar_Number_confidence')
                
                # sample_json_confidence['Adhaar_Number_confidence'] = statistics.mean(word_confidence)
                confidence_counter +=1
                #print('Adhaar counter', confidence_counter)

    # print("sample_json: ",sample_json)
    # print("sample_json_confidence: ",sample_json_confidence)
    try:
        sample_json['Accuracy'] = statistics.mean(sample_json_confidence.values())*100
    except Exception as e:
        logger.error("Error in accuracy", exc_info=True)
        
    sample_json['Bounding_Box'] = sentence_bbox
    #print("sentence bbox: ",sentence_bbox)
    return sample_json

# Processing the Aadhar Back side image(old format) with region language on left and english language with right side of the Aadhar

def adr_back(lines_data):
    # print("adr_back is called")
    confidence_counter = 0
    biggest_bbox_width = 0

    address_arr = []

    header_found = False

    import numpy as np
    conf_range = [round(val,2) for val in np.arange(0.61,0.75,0.01)]

    constant_keys = []

    # print(conf_range)
    for ld in lines_data:
        if fuzz.ratio("UNIQUE IDENTIFICATION AUTHORITY OF INDIA".lower(), ld['text'].lower()) > 90:
            lines_data = lines_data[lines_data.index(ld)+1:]
            header_found = True
            continue

        if header_found:
            conf = [var['confidence'] for var in ld['words'] if var['confidence']]
            conf_avg = sum(conf) / len(conf)

            #print(f"Parent text {ld['text']} {conf_avg}")
            if round(conf_avg,2) in conf_range:
                    modified_low_conf_score = conf_avg

                    for word_val in ld['words']:
                        if word_val['confidence'] >= modified_low_conf_score:
                            address_arr.append(word_val['text'])
                # print(conf_avg, lines_data.index(ld))
                # index_low_conf.append({str(lines_data.index(ld)): conf_avg})


            if conf_avg > 0.75:
                for word_og_dict in ld['words']:
                    address_arr.append(word_og_dict['text'])


    # for low_conf_idx in index_low_conf:
    #     low_conf_dict = lines_data[int(list(low_conf_idx.keys())[0])]
    #     modified_low_conf_score = low_conf_idx.get(list(low_conf_idx.keys())[0]) + 0.02
    #
    #     for word_val in low_conf_dict['words']:
    #         if word_val['confidence'] >= modified_low_conf_score:
    #             address_arr.append(word_val['text'])
    #print(address_arr)
    for final_val in address_arr:
        if final_val.isdigit() and len(final_val) == 6:
                if address_arr.count(final_val) > 1:
                    address_arr.remove(final_val)

                else:
                    address_arr = address_arr[:address_arr.index(final_val)+1]

        mod_final_val = re.sub(r'[^a-zA-Z0-9]','',final_val)
        #print(mod_final_val)
        if mod_final_val.isdigit() :
            #print(mod_final_val, final_val)
            if address_arr.count(final_val) > 1:
                address_arr.remove(final_val)



    # print(" ".join(address_arr))

    # print(header_found)
    return

# calling the aadhar back function
#adr_back(lines_data)

# Function for Processing the Aadhar backside of any format
def adr_back_get_address(image_back): # Pass the json data to the function
    data = azure_ocr.azure_call(image_back)
    lines_data = data['analyzeResult']['readResults'][0]['lines']
    logger.info(lines_data)
    sentence_bbox = {}
    front_or_back_address_check = adhaar_back_check(lines_data)
    if front_or_back_address_check:
        # print("Address is in the front")
        #print("front_or_back_address_check: ",front_or_back_address_check)
        address,address_confidence,final_address_confidence,sentence_bbox = adhaar_front_get_address(lines_data)
        # print("address: ",address,"address_confidence: ",address_confidence,"final_address_confidence:",final_address_confidence)
        return {'Address': address,"Bounding_Box":sentence_bbox, "Accuracy":final_address_confidence}
    if not front_or_back_address_check : #else
        # print("checking for back details")
        #print("lines_data: ",lines_data)
        #print("Inside the else because the address is in back ")
        width = data['analyzeResult']['readResults'][0]['width']
        xtl = 0
        ytl = 0
        xtr = 0
        ytr = 0
        xbr = 0
        ybr = 0
        xbl = 0
        ybl = 0
        global found_uidai #change
        found_uidai = False
        found_address = False
        found_pincode = False
        final_text = []
        condition = None
        address_left = False
        address_text = None
        address_with_word = None
        address_confidence = []
        uidai_index = None
        very_new_format = False
        for lines_idex, lines in enumerate(lines_data):
            #print(lines['text'],fuzz.ratio('UNIQUE IDENTIFICATION AUTHORITY OF INDIA'.lower(),lines['text'].lower()))
            if fuzz.ratio('UNIQUE'.lower(), lines['words'][0]['text'].lower()) > 95:
                uidai_index = lines_idex
                #print("lines['boundingBox'][0]: ",lines['boundingBox'][0])
                #print("width / 3: ",width / 3)
                threshold = abs(lines['boundingBox'][0] - (width / 3)) #2
                #print('threshold; ',threshold)
                #print("Found the UIDAI")
                xtl, ytl = lines['boundingBox'][0] + threshold, lines['boundingBox'][1]
                xtr, ytr = lines['boundingBox'][2], lines['boundingBox'][3]
                xbr, ybr = lines['boundingBox'][4], lines['boundingBox'][4]
                xbl, ybl = lines['boundingBox'][6] + threshold, lines['boundingBox'][7]
                #print("xtl from the very begining: ",xtl)
                #print("xtr from the very begining: ",xtr)
                found_uidai = True
                continue
            elif found_uidai:
                #print("inside the elif if found_uidai")
                for idx, words in enumerate(lines['words']):
                    #print("found_uidai: ",words['text'])
                    #print("idx: ",idx)
                    #print(words['text'],fuzz.ratio('Downloaded'.lower(),words['text'].lower()))
                    if fuzz.ratio('Download'.lower(), words['text'].lower()) >= 90:
                        very_new_format = True
                    else:
                        pass
                    if fuzz.ratio('ADDRESS'.lower(), words['text'].lower()) >= 90 and (
                            words['boundingBox'][0] <= xtl and words['confidence'] >= 0.60):
                        uidai_data = lines_data[uidai_index]
                        if very_new_format:
                            #print("Extreme new format")
                            threshold = abs(uidai_data['boundingBox'][0] - (width / 4))
                            xtl, ytl = uidai_data['boundingBox'][0], uidai_data['boundingBox'][1]
                            xtr, ytr = uidai_data['boundingBox'][2] - threshold, uidai_data['boundingBox'][3]
                            xbr, ybr = uidai_data['boundingBox'][4] - threshold, uidai_data['boundingBox'][4]
                            xbl, ybl = uidai_data['boundingBox'][6], uidai_data['boundingBox'][7]
                        if lines['boundingBox'][0] >= 100:
                            #print("Address in center")
                            threshold = abs(uidai_data['boundingBox'][0] - (width / 3.5))
                            xtl, ytl = uidai_data['boundingBox'][0], uidai_data['boundingBox'][1]
                            xtr, ytr = uidai_data['boundingBox'][2] - threshold, uidai_data['boundingBox'][3]
                            xbr, ybr = uidai_data['boundingBox'][4] - threshold, uidai_data['boundingBox'][4]
                            xbl, ybl = uidai_data['boundingBox'][6], uidai_data['boundingBox'][7]
                            # print(xtl,ytl  ,xtr ,ytr ,xbr ,ybr ,xbl ,ybl )
                        else:
                            xtl, ytl = uidai_data['boundingBox'][0], uidai_data['boundingBox'][1]
                            xtr, ytr = uidai_data['boundingBox'][2] - threshold, uidai_data['boundingBox'][3]
                            xbr, ybr = uidai_data['boundingBox'][4] - threshold, uidai_data['boundingBox'][4]
                            xbl, ybl = uidai_data['boundingBox'][6], uidai_data['boundingBox'][7]
                        address_left = True
                        # if address_left:
                        #     print("address in the left part of the image")
                        # else:
                        #     pass
                        # found_uidai = True
                    else:
                        pass
                        #print(words['text'],"words['boundingBox'][0]",words['boundingBox'][0],"words['confidence'] >=60:",words['confidence'] )
                    if idx >= 1:
                        #print("idx from if:",idx)
                        #print("lines['words'][idx-1]['text']:",lines['words'][idx-1]['text'])
                        #print("words['text'].lower()",words['text'].lower())
                        #print(fuzz.ratio(lines['words'][idx-1]['text'].lower(),words['text'].lower()))
                        if address_left:
                            #print("The address is in the left hand side of the image")
                            condition = (words['boundingBox'][0] <= xtr and words['confidence'] >= 0.60) or fuzz.ratio(
                                lines['words'][idx - 1]['text'].lower(), words['text'].lower()) > 90

                        else:
                            #print("The address is in the right hand side of the image")
                            #print(" words['text']", words['text'])
                            condition = (words['boundingBox'][0] >= xtl and words['confidence'] >= 0.60) or fuzz.ratio(
                                lines['words'][idx - 1]['text'].lower(), words['text'].lower()) > 90
                    else:
                        #print("idx from else:",idx)
                        #print("words['text']:===>",words['text'])
                        if address_left:
                            #print("The address is in the left hand side of the image")
                            condition = words['boundingBox'][0] <= xtr and words['confidence'] >= 0.60
                        else:
                            #print("The address is in the right hand side of the image",)
                            condition = words['boundingBox'][0] >= xtl  # and words['confidence'] >=0.60
                            #print("word: ",words['text'],"condition: ",condition,"xtl: ",xtl,"words['boundingBox'][0]: ",words['boundingBox'][0])
                    if condition:
                        #print("words",words)
                        #print("fuzz.ratio('ADDRESS'.lower(),words['text'].lower())",fuzz.ratio('ADDRESS'.lower(),words['text'].lower()))
                        #print("found_address",found_address)
                        if words['text'].lower().split(":")[0] == 'address':
                            address_text = words['text'].lower().split(":")[0]

                            address_with_word = True
                            #print("address_text",address_text)
                        else:
                            address_text = words['text'].lower()
                            #print("address_text",address_text)

                        if fuzz.ratio('ADDRESS'.lower(), address_text) >= 90 or found_address: #fuzz.ratio('ADDRESS'.lower(), words['text'].lower()) >= 90 or found_address
                            #print(words)
                            #print("words['boundingBox'][0]",words['boundingBox'][0],"words['confidence'] >=60:",words['confidence'] >=0.60)
                            if address_with_word:
                                try:
                                    text = words['text'].split(":")[1]
                                    address_with_word = False
                                except:
                                    text = ""
                                    #ext = words['text']
                                    address_with_word = False
                            else:
                                text = words['text']
                                #print('text from else',text)
                            #print(text.lower() != "address", text.lower().strip().split(":")[0] != "address")
                            if text.lower() != "address" and text.lower().strip().split(":")[0] != "address":
                                #print("address text: ",text)
                                #print("lines data from the address section:  ",lines)
                                regex = "^[1-9]{1}[0-9]{2}\\s{0,1}[0-9]{3}$"
                                p = re.compile(regex)
                                m = re.match(p, text)
                                if m:
                                    #print("m: ",m.group())
                                    #print("Text of lines data from the address section:  ",text)
                                    get_word_confidence_mean(new_data=lines,address_confidence=address_confidence,text=text)
                                    #print("lines['text'] from if m : ",lines['text'])
                                    avg_confidence = address_line_bbox_check(lines)
                                    if avg_confidence > 0.90: 
                                            sentence_bbox[lines['text']] = (lines['boundingBox'],str(round(avg_confidence*100))+"%")
                                    else:
                                        pass
                                    #sentence_bbox[lines['text']] = lines['boundingBox']
                                    found_pincode = True
                                else:
                                    if not found_pincode:
                                        #print("Text of lines data from the address section:  ",text)
                                        get_word_confidence_mean(new_data=lines,address_confidence=address_confidence,text=text)
                                        if lines['text'].lower() not in ['address:','address','address :']:
                                            #print("lines['text'] from if not found_pincode : ",lines['text'])
                                            avg_confidence = address_line_bbox_check(lines)
                                            if avg_confidence > 0.90: 
                                                sentence_bbox[lines['text']] = (lines['boundingBox'],str(round(avg_confidence*100))+"%")
                                            else:
                                                pass
                                        else:
                                            pass
                                final_text.append(text)
                            found_address = True
                        else:
                            pass
                    else:
                        continue
        #print(xtl, ytl, xtr, ytr, xbr, ybr, xbl, ybl)
        # print(final_text[:final_text.index('www')])
        for word in final_text:
            if word.isdigit() and len(word) == 6:
                final_text = final_text[:final_text.index(word)+1]
                # if word in sentence_bbox.keys():
                #     position =  sentence_bbox.keys().index(word)
            else:
                pass
        final_address = ' '.join(final_text)
        print("final_text",final_text)
        #print("sentence bbox: ",sentence_bbox)
        #print("final_address: ",final_address,'len(final_address) ',len(final_address.split()))
        #print("address_confidence: ",address_confidence,'len(address_confidence) ',len(address_confidence)
        if address_confidence:
            final_address_confidence = statistics.mean(address_confidence)*100
            return {'Address': final_address,"Bounding_Box":sentence_bbox,"Accuracy":final_address_confidence}
        #print("final_address_confidence: ",final_address_confidence)
        else:
            pass    
        #return {'Address': final_address, "Accuracy":final_address_confidence}
    if not found_uidai:
        print("Going for the plain ocr")
        final_address,final_address_confidence,sentence_bbox = plain_ocr(lines_data)
        print({'Address': final_address,"Bounding_Box":sentence_bbox,"Accuracy":final_address_confidence})
        return {'Address': final_address,"Bounding_Box":sentence_bbox,"Accuracy":final_address_confidence}


