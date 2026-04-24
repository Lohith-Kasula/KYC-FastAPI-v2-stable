
# Example Format of the azure resposne
# processed_azure_response = [('INCOME TAX DEPARTMENT', [[26,62],[84,62],[84,85],[25,84]]),
#  ('GOVT. OF INDIA', [[324,66],[386,67],[386,89],[323,89]]),
#  ('AJITH CHAND KANAGALA', [[40,98],[87,99],[87,115],[40,115]]),
#  ('VENKATA RAMA MOHAN CHAND', [[39,140],[115,140],[115,156],[40,155]]),
#  ('KANAGALA', [[38,155],[131,156],[131,171],[38,170]]),
#  ('03/05/1995', [[39,181],[126,181],[126,197],[39,197]]),
#  ('Permanent Account Number', [[39,201],[209,203],[209,216],[38,214]]) ,
#  ('DGLPK3432G', [[38,223],[161,224],[161,241],[38,240]]),
#  #('be Asith cher', [[37.0, 260.0], [163.0, 255.0], [165.0, 282.0], [38.0, 288.0]]),
#  #('Signature', [[37.0, 292.0], [99.0, 293.0], [99.0, 306.0], [37.0, 306.0]])
#  ]

from fuzzywuzzy import fuzz
def merge_bbox(lines_data_from_json):
    final_processed_azure_response = []
    processed_azure_response = []
    final_string = None
    final_bbox = None
    final_confidence = None
    step = 1
    # print(lines_data_from_json)
    for data_dict_idx in range(len(lines_data_from_json)):
        data_dict = lines_data_from_json[data_dict_idx]
        bbox = []
        text = data_dict['text']
        conf = [words_dict['confidence'] for words_dict in data_dict['words']]
        avg_conf = round(sum(conf)/len(conf),2)

        for idx in range(0,len(data_dict['boundingBox']),2): #2
            bbox.append([data_dict['boundingBox'][idx],data_dict['boundingBox'][idx+1]])
            #print(f"Text: {data_dict['text']} , Bbox: {[data_dict['boundingBox'][idx], data_dict['boundingBox'][idx+1]]}")
        processed_azure_response.append((text,bbox,avg_conf))
    #print("processed_azure_response: ",processed_azure_response)
    for idx1 in range(0,len(processed_azure_response)):   
        #print('step',step)
        #print('idx1',idx1)
        if step > 1:
            idx1 = idx1 + step-1
            #print('new idx1 because step > 1',idx1)
        for idx2 in range(idx1+1,len(processed_azure_response)+1):
            #print("idx2",idx2)
            #print("idx1",idx1,processed_azure_response[idx1][0],fuzz.ratio('Permanent Account Number',processed_azure_response[idx1][0]))
            if fuzz.ratio('Permanent Account Number',processed_azure_response[idx1][0]) >= 85:
                #print("found Permanent Account Number breaking the merge bbox logic")
                final_processed_azure_response.append(processed_azure_response[idx1])
                break
            if idx2 >= len(processed_azure_response):
                #print("breaking the merge bbox logic due to length")
                final_processed_azure_response.append(processed_azure_response[idx1]) 
                break
            if not final_string and not final_bbox:  
                threshold_1 = 3 #abs(processed_azure_response[idx1][1][3][1]- processed_azure_response[idx2][1][0][1]) - 2
                #print("threshold_1",threshold_1,"original: ",threshold_1+2)  
                threshold_2 = 3 #abs(processed_azure_response[idx1][1][3][0] - processed_azure_response[idx2][1][0][0]) - 2           
                #print("threshold_2",threshold_2,"original: ",threshold_2+2)
                if abs(processed_azure_response[idx1][1][3][1]- processed_azure_response[idx2][1][0][1]) <= threshold_1 and (abs(processed_azure_response[idx1][1][3][0] - processed_azure_response[idx2][1][0][0])<=threshold_2):#3,3
                    #print('into the inner if of the main if')
                   
                    new_text = processed_azure_response[idx1][0] +' '+ processed_azure_response[idx2][0]
                    new_confidence = round((processed_azure_response[idx1][2]+processed_azure_response[idx2][2])/2,2)
                    #print('New Confidence processed_azure_response[idx1][2] + processed_azure_response[idx2][2]',processed_azure_response[idx1][2],'<=>',processed_azure_response[idx2][2])
                    tl = processed_azure_response[idx1][1][0]
        
                    tr = processed_azure_response[idx1][1][1]
                    
                    br = [processed_azure_response[idx1][1][2][0],processed_azure_response[idx1][1][2][1]+abs(processed_azure_response[idx1][1][2][1]-processed_azure_response[idx2][1][2][1])]
                    
                    bl = [processed_azure_response[idx1][1][3][0],processed_azure_response[idx1][1][3][1]+abs(processed_azure_response[idx1][1][3][1]-processed_azure_response[idx2][1][3][1])]
                  

                    new_bbox = [tl,tr,br,bl]
                    
                    final_string = new_text
                    #print("final_string: ",final_string)
                    final_bbox = new_bbox
                    #print("final bbox: ",final_bbox)
                    final_confidence = new_confidence

                    step +=1

                else:            
                    final_processed_azure_response.append(processed_azure_response[idx1])
                    break
            else:
                #print(final_bbox[3][1],processed_azure_response[idx2][1][0][1],(final_bbox[3][1]- processed_azure_response[idx2][1][0][1]),(processed_azure_response[idx2][1][0][1] < final_bbox[3][1]))
                threshold_1 = 2#(final_bbox[3][1]-processed_azure_response[idx2][1][0][1])-2 #3
                #print("threshold_1",threshold_1,"original: ",threshold_1-2)
                if abs(processed_azure_response[idx2][1][0][1]-final_bbox[3][1]) <= threshold_1 and (processed_azure_response[idx2][1][0][1] < final_bbox[3][1]):
                    #print("inside the else part if of the main if")
                    new_text = final_string +' '+ processed_azure_response[idx2][0] 
                    new_confidence = round((final_confidence+processed_azure_response[idx2][2])/2,2)
                    
                    tl = final_bbox[0]
                
                    tr = final_bbox[1]
                    
                    br = [final_bbox[2][0],final_bbox[2][1]+abs(final_bbox[2][1]-processed_azure_response[idx2][1][2][1])]
                
                    bl = [final_bbox[3][0],final_bbox[3][1]+abs(final_bbox[3][1]-processed_azure_response[idx2][1][3][1])]
            

                    new_bbox = [tl,tr,br,bl]
                    
                    final_string = new_text
                    #print("final_string:",final_string)
                    final_bbox = new_bbox
                    final_confidence = new_confidence
                   
                    
                    step +=1

                else:
                    #print('into the inner else of main else')
                    final_append = (final_string,final_bbox,final_confidence)
                    final_processed_azure_response.append(final_append)
                    final_string = None
                    final_bbox = None
                    final_confidence = None
                    #print('final_processed_azure_response from the inner else of main else: ',final_processed_azure_response)
                    break
        
    return final_processed_azure_response

        






