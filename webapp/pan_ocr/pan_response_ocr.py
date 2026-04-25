from multiprocessing import Condition
import re
from fuzzywuzzy import fuzz
from pan_ocr import merge_bbox
import itertools
import statistics
import logging

logger = logging.getLogger(__name__)
uvicorn_logger = logging.getLogger(__name__)

'''
PAN Validation checks:
1. Income Tax Department
2. Govt of India
3. PAN Number: 
It should be ten characters long.
The first five characters should be any upper case alphabets.
The next four-characters should be any number from 0 to 9.
The last(tenth) character should be any upper case alphabet.
It should not contain any white spaces.
and the 4th character should be among these 
                A — Association of persons (AOP)
                B — Body of individuals (BOI)
                C — Company
                F — Firm
                G — Government
                H — HUF (Hindu undivided family)
                L — Local authority
                J — Artificial juridical person
                P — Person (Individual)
                T — Trust (AOP)


'''
entity_type =   {'A' : 'Association of persons (AOP)',
                'B' : 'Body of individuals (BOI)',
                'C' : 'Company',
                'F' : 'Firm',
                'G' : 'Government',
                'H' : 'HUF (Hindu undivided family)',
                'L' : 'Local authority',
                'J' : 'Artificial juridical person',
                'P' : 'Person (Individual)',
                'T' : 'Trust (AOP)'}

#accepted_keys = ['Permanent Account Number Card', 'Name', "Father's Name", 'Date of Birth']
accepted_keys = ['Permanent Account Number Card', 'Name', "Father's Name", 'Date of Birth','Date of Incorporation']
sample_json_confidence = {"Name_confidence":'',"Father's_Name_Confidence":'','Pan_confidence':'','DOB/DOI_confidence':''}

def pan_accuracy(new_data,sample_json_confidence=None,key=None,text=None):
    word_confidence = []
    #print("len(new_data['text'].split())",new_data)
    # for idx in range(0,len(new_data['text'].split())):
    #     if new_data['words'][idx]['text'] == new_data['text'].split()[idx] :
    #print("new_data['text'] == text",new_data,"text: ",text)
    if new_data['text'] == text:
        word_confidence.append(new_data['confidence'])
    #print("word_confidence: ",word_confidence,'text: ',text)
    if word_confidence:
        sample_json_confidence[key] = statistics.mean(word_confidence)
    else:
        pass
    return 

def isPANValid(pan_num):
    Result = re.compile("[A-Z]{3}[ABCFGHLJPTK]{1}[A-Z]{1}[0-9]{4}[A-Z]{1}")  # [A-Za-z]{5}\d{4}[A-Za-z]{1}

    return Result.search(pan_num)


def get_word_bbox_with_conf(lines_data,sentence):
    #print("lines_data from get_word_bbox_with_conf",lines_data)
    found_sentence_index = None
    each_word_bbox = []
    for idx,value in enumerate(lines_data):
        
        if value['text'] in sentence:
            found_sentence_index = idx
            for item in lines_data[found_sentence_index]['words']:
                if len(each_word_bbox) < len(sentence.split()):
                    #print("item['text']: ",item['text'],'sentence: ',sentence)
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

    

# 2. Key value pairs NEW format PAN card, which has Key's on the card

def newformatPAN(data,is_company,is_veryold,og_lines_data):
    #print("is_company: ",is_company,"is_veryold",is_veryold)
    sample_json_confidence = {"Name_confidence":'',"Father's_Name_Confidence":'','Pan_confidence':'','DOB/DOI_confidence':''}
    #print("data: ",data)
    sentence_bbox = {}
    new_kv_map = {}
    try:
        if is_veryold:
            accepted_keys[accepted_keys.index('Name')] = 'NAME'
            accepted_keys[accepted_keys.index("Father's Name")] = "FATHER'S NAME"
            accepted_keys[accepted_keys.index('Date of Birth')] = 'DATE OF BIRTH'
            accepted_keys[accepted_keys.index('Date of Incorporation')] = 'DATE OF INCORPORATION'
        else:
            accepted_keys[accepted_keys.index('Name')] = 'Name'
            accepted_keys[accepted_keys.index("Father's Name")] = "Father's Name"
            accepted_keys[accepted_keys.index('Date of Birth')] = 'Date of Birth'
            accepted_keys[accepted_keys.index('Date of Incorporation')] = 'Date of Incorporation'  
    except:
        pass
    for k in accepted_keys:
        for var in data:
            #print(f"og Text: {k} , Text found: {var['text']}", fuzz.ratio(k, var['text']))
            if "name" in var['text'].lower() and "/" in var["text"] :
                #print("name: ",data.index(var))
                var['text'] = var['text'].split("/")[1]
            #print(fuzz.ratio(k, var['text']))
            if fuzz.ratio(k,var['text']) > 50:
                #print(k, var['text'])
                if is_veryold: 
                    #print('k from the DOB if condition ',k,'Date of Birth'.upper())
                    Condition_check =  (k == 'Date of Birth'.upper()) or (k == 'Date of Incorporation'.upper())
                    #print("Condition_check if : ",Condition_check)
                else :
                    Condition_check =  (k == 'Date of Birth') or (k == 'Date of Incorporation')
                    #print("Condition_check else : ",Condition_check)
                if Condition_check: #(k == 'Date of Birth') or (k == 'Date of Incorporation')
                    #print("getting the date")
                    for dates in data[data.index(var)+1:]:
                        if is_veryold: 
                            #print("checking the  date pattern")
                            date_pattern = r'(\d{2}-\d{2}-\d{4})'
                        else:
                          date_pattern = r'(\d{2}/\d{2}/\d{4})'  
                        match_date = re.match(date_pattern,dates['text'])
                        #print("match found: ",match_date)
                        try:
                            date_found = match_date.group()
                            if is_company:
                                text = date_found
                                pan_accuracy(new_data=dates,sample_json_confidence=sample_json_confidence,key='DOB/DOI_confidence',text=text)
                                new_kv_map['DOI'] = date_found
                                #sentence_bbox['DOI'] = dates['boundingBox']
                                sentence_bbox['DOI'] = get_word_bbox_with_conf(og_lines_data,text)
                            else:
                                #print("setting the DOB")
                                text = date_found
                                pan_accuracy(new_data=dates,sample_json_confidence=sample_json_confidence,key='DOB/DOI_confidence',text=text)
                                new_kv_map['DOB'] = date_found
                                #sentence_bbox['DOB'] = dates['boundingBox']
                                sentence_bbox['DOB'] = get_word_bbox_with_conf(og_lines_data,text)
                            #print(k, match_date.group())
                        except:
                            continue
                else:
                    if is_veryold:
                        pan_check_string = 'PERMANENT ACCOUNT NUMBER'
                    else:
                       pan_check_string = 'Permanent Account Number Card'
                    if k == pan_check_string : # k == 'Permanent Account Number Card'

                        validating_pan = isPANValid(data[data.index(var)+1]['text']) # validating the pan number here
                        if validating_pan is None:
                            validating_pan = isPANValid(data[data.index(var)+2]['text'])
                        else:
                            pass
                        if (validating_pan):
                            text = validating_pan.group()
                            pan_accuracy(new_data=data[data.index(var)+1],sample_json_confidence=sample_json_confidence,key="Pan_confidence",text=text)
                            new_kv_map["PAN_Number"] = validating_pan.group()
                            #sentence_bbox['PAN_Number'] = data[data.index(var)+1]['boundingBox']
                            sentence_bbox['PAN_Number'] = get_word_bbox_with_conf(og_lines_data,text)
                            #print(k, validating_pan.group())
                        else:
                            new_kv_map["PAN_Number"] = "NA"
                            
                    else:
                        #print(k, data[data.index(var) + 1]['text'])
                        if is_veryold:
                            #print("k: ",k)
                            if k == 'NAME':
                                #print("k == NAME",k)
                                Name_conditon_1 = 'NAME'
                            elif k == "FATHER'S NAME":
                                #print("k == FATHER'S NAM",k)
                                Name_conditon_2 = "FATHER'S NAME"
                        else:
                            if k == 'Name':
                                Name_conditon_1 = 'Name'
                            elif k == "Father's Name":
                                 Name_conditon_2 = "Father's Name"
                        if k == Name_conditon_1: #k == 'Name'
                            #print("Name_conditon_1", Name_conditon_1)
                            if is_company :
                                text = data[data.index(var) + 1]['text']
                                pan_accuracy(new_data=data[data.index(var) + 1],sample_json_confidence=sample_json_confidence,key='Name_confidence',text=text)
                                new_kv_map["Company_Name"] = data[data.index(var) + 1]['text']
                                #sentence_bbox['Company_Name'] =  data[data.index(var) + 1]['boundingBox']
                                sentence_bbox['Company_Name'] = get_word_bbox_with_conf(og_lines_data,text)
                            else:
                                #print("getting the first name",data[data.index(var) + 1]['text'])
                                text = data[data.index(var) + 1]['text']
                                pan_accuracy(new_data=data[data.index(var) + 1],sample_json_confidence=sample_json_confidence,key='Name_confidence',text=text)
                                new_kv_map["First_Name"] = data[data.index(var) + 1]['text']
                                #sentence_bbox['Name'] =  data[data.index(var) + 1]['boundingBox']
                                sentence_bbox['Name'] = get_word_bbox_with_conf(og_lines_data,text)
                        elif k == Name_conditon_2: # k == "Father's Name" #"Father's Name"
                            #print("Name_conditon_2 from else", Name_conditon_2)
                            #print("getting the Father's name",data[data.index(var) + 1]['text'])
                            text = data[data.index(var) + 1]['text']
                            pan_accuracy(new_data=data[data.index(var) + 1],sample_json_confidence=sample_json_confidence,key="Father's_Name_Confidence",text=text)
                            new_kv_map["Fathers_Name"] = data[data.index(var) + 1]['text']
                            #sentence_bbox["Father's_Name"] =  data[data.index(var) + 1]['boundingBox']
                            sentence_bbox["Father's_Name"] = get_word_bbox_with_conf(og_lines_data,text)
             #final_values.append((data['text'], round(sum(conf)/len(conf), 2)))
            #print(data['text'], conf) #sum(conf)/len(conf)
            #print(final_values)
    #print(fuzz.ratio(accepted_keys[final_values.index(values)].lower(), values.lower()))

    #print(new_kv_map)

    if new_kv_map['PAN_Number'] != "NA":
        entity = new_kv_map['PAN_Number'][3]
        # print("entity",entity)
        # print(' entity_type[entity]', entity_type[entity])
        new_kv_map['Entity_Type'] = entity_type[entity]
        
    else:
        new_kv_map['Entity_Type'] = "NA"
        # print("Entity type not found")
    new_kv_map['Is_company'] = is_company
    #print("new_kv_map: ",new_kv_map)
    #print("sample_json_confidence: ",sample_json_confidence)
    #print("sentence_bbox: ",sentence_bbox)
    #print("sentence_bbox: ",sentence_bbox)
    if is_company:
        final_sentence_bbox = {}
        final_sentence_bbox['PAN_Number'] = sentence_bbox['PAN_Number']
        final_sentence_bbox['Name'] = sentence_bbox['Company_Name']
        final_sentence_bbox['DOI'] = sentence_bbox['DOI']
        new_kv_map['Bounding_Box'] = final_sentence_bbox
    else:
        new_kv_map['Bounding_Box'] = sentence_bbox
    try:
        new_kv_map['Accuracy'] = statistics.mean([i for i in sample_json_confidence.values() if i])*100
    except Exception as e:
        # logger.error("Error in accuracy",exc_info=True)
        new_kv_map['Accuracy'] = ''
    #new_kv_map['Bounding_Box'] = sentence_bbox
    return new_kv_map

# 3. Key Value pairs on OLD format PAN card, which has no Key's on it.
def oldformatPAN(data,is_company,og_lines_data):
    sample_json_confidence = {"Name_confidence":'',"Father's_Name_Confidence":'','Pan_confidence':'','DOB/DOI_confidence':''}
    sentence_bbox = {}
    #print(data)
    if is_company:
        #print("is_company: ",is_company)
        kv_map = {'Company_Name': ""}
    else:
        #print("is_company: ",is_company)
        kv_map = {'First_Name': "", 'Fathers_Name':""}

    for var in data:
        if fuzz.ratio("INCOME TAX DEPARTMENT", var['text']) > 90 or fuzz.ratio("GOVT. OF INDIA", var['text']) > 90:
            continue
        else:
            for k in kv_map.keys():               
                if not kv_map[k]:
                    kv_map[k] = var['text']
                    if k == 'First_Name':
                        #sentence_bbox['Name'] = var['boundingBox']
                        sentence_bbox['Name'] = get_word_bbox_with_conf(og_lines_data, var['text'])
                        pan_accuracy(new_data=var,sample_json_confidence=sample_json_confidence,key='Name_confidence',text=var['text'])
                    elif k == 'Fathers_Name':
                        #sentence_bbox["Father's_Name"] = var['boundingBox']
                        sentence_bbox["Father's_Name"] = get_word_bbox_with_conf(og_lines_data, var['text'])
                        pan_accuracy(new_data=var,sample_json_confidence=sample_json_confidence,key="Father's_Name_Confidence",text=var['text'])
                    elif k == 'Company_Name':
                        #sentence_bbox[k] = var['boundingBox']
                        sentence_bbox[k] = get_word_bbox_with_conf(og_lines_data, var['text'])
                        pan_accuracy(new_data=var,sample_json_confidence=sample_json_confidence,key="Name_confidence",text=var['text'])
                    #print("kv_map[k]",kv_map[k],k)
                    break
        #print(last_elm)
        if fuzz.ratio("Permanent Account Number", var['text']) > 90:
            # Eliminating the last text elements
            #final_values.append((data['text'], round(sum(conf) / len(conf), 2)))
            # if (''.join(var['text'].split()).isalnum()):
            #     print("var[text] from old panformat PAN condition",var['text'],var['text'].split()[-1])
            #     validating_pan = isPANValid(var['text'].split()[-1])
            # else: 
            #     print("var[text] from else old panformat PAN condition",var['text'],data[data.index(var)+1]['text'])               
            validating_pan = isPANValid(data[data.index(var)+1]['text'])  # validating the pan number here
            if validating_pan is None:
               validating_pan = isPANValid(data[data.index(var)+2]['text']) 
            else:
                pass
            if (validating_pan):
                kv_map['PAN_Number'] = validating_pan.group()
                # if (''.join(var['text'].split()).isalnum()):
                #     sentence_bbox['PAN_Number'] = data[data.index(var)]['boundingBox']
                # else:
                #     sentence_bbox['PAN_Number'] = data[data.index(var)+1]['boundingBox']
                #sentence_bbox['PAN_Number'] = data[data.index(var)+1]['boundingBox']
                sentence_bbox['PAN_Number']=get_word_bbox_with_conf(og_lines_data, data[data.index(var)+1]['text'])
                text = validating_pan.group()
                pan_accuracy(new_data=data[data.index(var)+1],sample_json_confidence=sample_json_confidence,key='Pan_confidence',text=text)
                # print(validating_pan.group())
            else:
                kv_map['PAN_Number'] = "NA"
                # print("Invalid PAN Number entered.")
        else:
            date_pattern = r'(\d{2}/\d{2}/\d{4})'
            match_date = re.match(date_pattern, var['text'])
            try:
                #match_date.group()
                if is_company:
                    kv_map['DOI'] = match_date.group()
                    #sentence_bbox['DOI'] = var['boundingBox']
                    text = match_date.group()
                    sentence_bbox['DOI'] = get_word_bbox_with_conf(og_lines_data,text)
                    pan_accuracy(new_data=var,sample_json_confidence=sample_json_confidence,key='DOB/DOI_confidence',text=text)

                else:
                    kv_map['DOB'] = match_date.group()
                    #sentence_bbox['DOB'] = var['boundingBox']
                    text = match_date.group()
                    sentence_bbox['DOB'] = get_word_bbox_with_conf(og_lines_data,text)
                    pan_accuracy(new_data=var,sample_json_confidence=sample_json_confidence,key='DOB/DOI_confidence',text=text)

                #print(match_date.group())
            except:
                continue
    #print(kv_map)

   # final_values = []
    # print("Total length of Kesy: ", len(json_data['analyzeResult']['readResults'][0]['lines']), '\n')
    # var = json_data['analyzeResult']['readResults'][0]['lines']

    # # print(data['text'])
    # final_values.append((data['text'], round(sum(conf)/len(conf), 2)))
    # #print(data['text'], sum(conf)/len(conf))
    # last_elm = data['text']

    if  kv_map['PAN_Number'] != "NA":
        entity = kv_map['PAN_Number'][3]
        # print("entity", entity)
        # print(' entity_type[entity]', entity_type[entity])
        kv_map['Entity_Type'] = entity_type[entity]

    else:
        kv_map['Entity_Type'] = "NA"
    kv_map['Is_company'] = is_company    
    #print('kv_map: ',kv_map)
    #print("sample_json_confidence: ",sample_json_confidence)
    #print("sentence_bbox: ",sentence_bbox)
    if is_company:
        final_sentence_bbox = {}
        final_sentence_bbox['PAN_Number'] = sentence_bbox['PAN_Number']
        final_sentence_bbox['Name'] = sentence_bbox['Company_Name']
        final_sentence_bbox['DOI'] = sentence_bbox['DOI']
        kv_map['Bounding_Box'] = final_sentence_bbox
    else:
        kv_map['Bounding_Box'] = sentence_bbox
    kv_map['Accuracy'] = statistics.mean([i for i in sample_json_confidence.values() if i])*100
    # kv_map['Bounding_Box'] = sentence_bbox
    return kv_map


def config_jsonfile(array_text,og_lines_data):
    #print("array_text: ",array_text)
    #final_values = []
    # print("Total length of Keys: ", len(json_data['analyzeResult']['readResults'][0]['lines']),'\n')
    # var = json_data['analyzeResult']['readResults'][0]['lines']
    #extreme old pan card check
    Upper_range = None
    Lower_range = None
    is_company = False
    is_veryold = False
    try:
        #print("array_text[0]['text'].split('/')[1]",array_text[0]['text'].split('/')[1])
        if array_text[0]['text'].split('/')[1] == 'PERMANENT ACCOUNT NUMBER':
            accepted_keys[0] = 'PERMANENT ACCOUNT NUMBER'
            is_veryold = True
            Lower_range = 0
        else:
            accepted_keys[0] = 'Permanent Account Number Card'
            accepted_keys[1] = 'Name'
            accepted_keys[2] = "Father's Name"
            accepted_keys[3] = 'Date of Birth'
            accepted_keys[4] = 'Date of Incorporation' 
            
    except :
        #print("inside the except of config file")
        accepted_keys[0] = 'Permanent Account Number Card'
        accepted_keys[1] = 'Name'
        accepted_keys[2] = "Father's Name"
        accepted_keys[3] = 'Date of Birth'
        accepted_keys[4] = 'Date of Incorporation' 
    #print("accepted_keys after modification",accepted_keys)
    for data in array_text:
        # conf = [var1['confidence'] for var1 in data['words'] if var1['confidence'] > 0.95]
        for k in accepted_keys: 
            #print("k from config json",k,data['text'],fuzz.ratio(k, data['text']))
            if is_veryold:
                  fuzzy_threshold = 80
            else:
                fuzzy_threshold = 90

            # if (''.join(data['text'].split()).isalnum()):
            #     target_text =  ' '.join(data['text'].split()[:-1])
            # else:
            #     target_text = data['text']
            #print("Threshold:=>",fuzzy_threshold,"k:+>",k,"data['test']",data['text'],"fuzz_ratio:=>",fuzz.ratio(k, data['text']))   
            if fuzz.ratio(k, data['text']) > fuzzy_threshold and (k == 'Permanent Account Number Card' or k == 'PERMANENT ACCOUNT NUMBER'): #fuzz.ratio(k, data['text']) > 90
                #print("passed the fuzzy ratio threshold",array_text[array_text.index(data)+1]['text'])
                # if (''.join(data['text'].split()).isalnum()):
                #     target_text =  ' '.join(data['text'].split()[:-1])
                #     validating_pan = isPANValid(data['text'].split()[-1])
                # else:
                #     validating_pan = isPANValid(array_text[array_text.index(data)+1]['text'])
                validating_pan = isPANValid(array_text[array_text.index(data)+1]['text'])
                #print("validating_pan: ",validating_pan)
                if validating_pan is None:
                    validating_pan = isPANValid(array_text[array_text.index(data)+2]['text'])
                else:
                    pass
                if validating_pan:
                    #print("pan is a valid pan")
                    pan_number = validating_pan.group()
                    entity = pan_number[3]
                    #print("entity",entity)
                    # print(' entity_type[entity]', entity_type[entity])
                    entity = entity_type[entity]
                    if entity != 'Person (Individual)':
                        #print("non individual or person format")
                        #print("is_veryold:",is_veryold)
                        Upper_range = 4
                        is_company = True
                        if not is_veryold:
                            Lower_range = 2
                        else:
                            pass
                    else:
                        #print("personal (Individual)")
                        Upper_range = 5
                        #print("is_veryold:",is_veryold)
                        if not is_veryold:
                            Lower_range = 2
                        else:
                            pass
                try:
                    if array_text.index(data) in range(Lower_range,Upper_range) : #rescent) array_text.index(data) in range(2,Upper_range) # 1) array_text.index(data) in range(2,5)
                        uvicorn_logger.info("New format PAN Card")
                        final_values =  newformatPAN(array_text,is_company,is_veryold,og_lines_data)
                        
                    elif array_text.index(data) in range(Upper_range,8): #array_text.index(data) in range(5,8)
                        uvicorn_logger.info("Old Format PAN card")
                        final_values = oldformatPAN(array_text,is_company,og_lines_data)

                except Exception as e:
                    logger.error("Could not detect format", exc_info=True)
                    final_values = oldformatPAN(array_text,is_company,og_lines_data)
                
                    #print(k, data['text'], fuzz.ratio(k, data['text']), final_values[final_values.index(data['text']) + 1])
    return final_values

def map_kv_pairs(json_data):
    #print(json_data)

    # Reading the json data, which is obtained from the azure ocr api
    # with open(f'../{file_name}.json', 'w') as out_F:
    #     json_data = json.load(file)

    #print("Total length of Keys: ", len(json_data['analyzeResult']['readResults'][0]['lines']), '\n')
    lines_data = json_data['analyzeResult']['readResults'][0]['lines']
    
    merge_cond = True

    # lines_data = [v for v in lines_data  \
    #               if fuzz.ratio("INCOME TAX DEPARTMENT", v['text']) > 90]
    # lines_data = lines_data[lines_data.index(data)]
    for ld in lines_data:
        if fuzz.ratio("INCOME TAX DEPARTMENT", ld['text']) > 90:
            lines_data = lines_data[lines_data.index(ld):]

    for data in lines_data:
        conf = [var['confidence'] for var in data['words'] if var['confidence']]
        conf_avg = sum(conf)/len(conf)

        if conf_avg < 0.60:
            lines_data.remove(data)
    # print(lines_data, conf_avg)
    #old_data = lines_data
    #print("\n lines data: ", lines_data)
    og_lines_data = lines_data
    # Check if new PAN format
    new_format_keys_found = [og_k for og_k in accepted_keys for line_val in lines_data \
                             if "/" in line_val['text']
                             if fuzz.ratio(og_k,line_val['text'].split("/")[1]) > 70]

    # remove duplicate values
    new_format_keys_found = list(set(new_format_keys_found))

    # Merge bbox only if PAN is of OLD format
    if len(new_format_keys_found) > 1:
        merge_cond = False

    if merge_cond:
        processed_results = merge_bbox.merge_bbox(lines_data)

    else:
        #print("\n lines data: ", lines_data)
        processed_results = lines_data

    #processed_results = lines_data
    #print("\n processed data: ", processed_results)

    final_json_arr = []

    for new_idx, new_val in enumerate(processed_results):
        new_json_format = {"text":"", "boundingBox":"", "confidence":""}
        #print("\n old lines data: ", lines_data[new_idx]['text'])
        #print("new_idx: ",new_idx,"new_val: ",new_val)
        #If old PAN format
        if merge_cond:
            new_json_format['text'] = processed_results[new_idx][0]
            new_json_format['boundingBox'] = list(itertools.chain.from_iterable(processed_results[new_idx][1]))
            new_json_format['confidence'] = processed_results[new_idx][2]

        #If new PAN format
        else:
            new_json_format['text'] = processed_results[new_idx]['text']
            new_json_format['boundingBox'] = processed_results[new_idx]['boundingBox']
            conf = [words_dict['confidence'] for words_dict in lines_data[new_idx]['words']]
            avg_conf = round(sum(conf) / len(conf), 2)
            new_json_format['confidence'] = avg_conf


        final_json_arr.append(new_json_format)
        # lines_data[new_idx]['text'] = processed_results[new_idx][0]
        #print("\n new lines data: ", lines_data[new_idx]['text'])
        # lines_data[new_idx]['boundingBox'] = list(itertools.chain.from_iterable(processed_results[new_idx][1]))
        #print("new json format :", new_json_format)

        # lines_data[new_idx]['text'] = processed_results[new_idx][1]
    # Temp file for storing new data
    lines_data = final_json_arr
    # with open("../temp1.json", "w") as temp_file:
    #     json.dump(lines_data, temp_file, indent=4)
    #
    # print(" \n old: ",old_data)
    #print("\n new: ", lines_data)
    json_results = config_jsonfile(lines_data,og_lines_data)
    return json_results
