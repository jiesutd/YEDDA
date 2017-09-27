# -*- coding: utf-8 -*-
# @Author: Jie
# @Date:   2017-04-25 11:07:00
# @Last Modified by:   Jie Yang,     Contact: jieynlp@gmail.com
# @Last Modified time: 2017-09-19 16:06:59
 

import re
import sys
import numpy as np

def lines_to_label_list(input_lines):
    label_list = []
    label = []
    for line in input_lines:
        if len(line) < 2:
            if len(label) > 0 :
                label_list.append(label)
            label = []
        else:
            label.append(line.strip().split()[-1])
    return label_list


## compare two files by f1-value, input file should be .ann file 
## with format [@word1#entity-type*]word2 word3 ...
## support nested entity (only use the largest span)
## already remove segmentation space, i.e. character based entity extraction (to avoid segmentation mismatch problem on two files)
def compare_files(gold_file, pred_file, up_ignore_layer = 0):
    # print "Compare files..."
    # print "Gold file:", gold_file
    # print "Pred file:", pred_file
    gold_entity, pred_entity, match_entity = get_matched_ner_from_file(gold_file, pred_file, up_ignore_layer)

    match_num = len(match_entity)
    gold_num = len(gold_entity)
    pred_num = len(pred_entity)
    return get_final_score(gold_num, pred_num, match_num)


def get_final_score(gold_num, pred_num, match_num):
    if pred_num == 0:
        precision = "Nan"
    else:
        precision =  (match_num+0.0)/pred_num
    if gold_num == 0:
        recall = 'Nan'
    else:
        recall = (match_num+0.0)/gold_num
    if (precision == "Nan") or (recall == "Nan") or (precision+recall) <= 0.0:
        f_measure = "Nan"
    else:
        f_measure = 2*precision*recall/(precision+recall)
    # print(('Precision: %s/%s = %s')%(match_num, pred_num, precision))
    # print(('Recall: %s/%s = %s')%(match_num, gold_num, recall))
    # print(('F1_value: %s')%(f_measure))
    return precision, recall, f_measure




def get_matched_ner_from_file(gold_file, pred_file, up_ignore_layer = 0):
    gold_lines = open(gold_file, 'rU').readlines()
    pred_lines = open(pred_file, 'rU').readlines()
    sentence_num = len(gold_lines)
    assert(sentence_num == len(pred_lines))
    gold_entity = []
    pred_entity = []
    match_entity = []
    start_line = 0
    end_line = start_line + 1000000
    for idx in range(sentence_num):
        if idx >= end_line:
            continue
        if idx < start_line:
            continue
        # print gold_lines[idx]
        gold_filter_entity = filter_entity(get_ner_from_sentence(gold_lines[idx]), up_ignore_layer)
        # print "gold:", gold_filter_entity
        pred_filter_entity = filter_entity(get_ner_from_sentence(pred_lines[idx]), up_ignore_layer)
        # print "pred:",pred_filter_entity
        match = list(set(gold_filter_entity).intersection(set(pred_filter_entity)))
        gold_entity += gold_filter_entity
        pred_entity += pred_filter_entity
        match_entity += match 
    return gold_entity, pred_entity, match_entity


def compare_f_measure_by_type(gold_file, pred_file):
    ## generate entity f score by entity type
    gold_entity, pred_entity, match_entity = get_matched_ner_from_file(gold_file, pred_file, 0)
    gold_type_dict = {}
    pred_type_dict = {}
    match_type_dict = {}
    for entity in gold_entity:
        entity_type = entity.split(':')[1]
        if entity_type in gold_type_dict:
            gold_type_dict[entity_type] += 1
        else:
            gold_type_dict[entity_type] = 1
    for entity in pred_entity:
        entity_type = entity.split(':')[1]
        if entity_type in pred_type_dict:
            pred_type_dict[entity_type] += 1
        else:
            pred_type_dict[entity_type] = 1
    for entity in match_entity:
        entity_type = entity.split(':')[1]
        if entity_type in match_type_dict:
            match_type_dict[entity_type] += 1
        else:
            match_type_dict[entity_type] = 1
    final_prf = []
    for entity in sorted(gold_type_dict.keys()):
        gold_num = gold_type_dict[entity]
        pred_num = 0
        match_num = 0
        if entity in pred_type_dict:
            pred_num = pred_type_dict[entity]
        if entity in match_type_dict:
            match_num = match_type_dict[entity]
        p,r,f = get_final_score(gold_num,pred_num, match_num)
        final_prf.append(entity + ":" + p_r_f_string(p,r,f))
    over_gold_num = len(gold_entity)
    over_pred_num = len(pred_entity)
    over_match_num = len(match_entity)
    p,r,f = get_final_score(over_gold_num, over_pred_num, over_match_num)
    final_prf.append("Overall" + ":" + p_r_f_string(p,r,f))

    ## get f measure for chunk
    gold_entity, pred_entity, match_entity = get_matched_ner_from_file(gold_file, pred_file, 2)
    over_gold_num = len(gold_entity)
    over_pred_num = len(pred_entity)
    over_match_num = len(match_entity)
    p,r,f = get_final_score(over_gold_num, over_pred_num, over_match_num)
    final_prf.append("Chunk" + ":" + p_r_f_string(p,r,f))

    return final_prf






def get_ner_from_sentence(sentence):
    ## remove segmentation space, avoid segmentation changes
    sentence = sentence.strip().replace(' ', '').decode('utf-8')
    sentence_len = len(sentence)
    # print sentence
    entity_start = []
    words = []
    last_char = ''
    entity_type_start = False
    entity_type = ''
    word_id = 0
    entity_list = []
    for idx in range(sentence_len):
        if sentence[idx] == '[':
            left_bracket = True 
        elif sentence[idx] == '@':
            if last_char == '[':
                entity_start.append(word_id)
            else:
                words.append(sentence[idx])
                word_id += 1
        elif sentence[idx] == '#':
            if len(entity_start) > 0:
                entity_type_start = True
            else:
                words.append(sentence[idx])
                word_id += 1
        elif sentence[idx] == ']':
            if last_char == '*':
                ## remove inside nested entity
                if len(entity_start) > 1:
                    entity_start.pop()
                    entity_type = ''
                    entity_type_start = False
                elif len(entity_start) == 1:
                    entity_info = '['+str(entity_start[0])+','+str(word_id-1) +']:'+entity_type.strip('*')
                    entity_list.append(entity_info.encode('utf-8'))
                    entity_type = ''
                    entity_start = []
                    entity_type_start = False
                else:
                    words.append(sentence[idx])
                    word_id += 1
        else:
            if entity_type_start:
                entity_type += sentence[idx]
            else:
                words.append(sentence[idx])
                word_id += 1
        last_char = sentence[idx]
    # print entity_list
    return entity_list
    # print entity_list
    # for word in words:
    #     print word, " ",

def filter_entity(entity_list, up_ignore_layer = 0):
    ## ignore entity type when calculate
    ignore_type = {}
    # ignore_type = {'Fin-Concept'}
    ## rename entity type
    # rename_type = {'Person-Name':'Person'}
    rename_type = {}
    filtered_list = []
    for entity in entity_list:
        pair = entity.split(':')
        entity_type = pair[-1]
        if entity_type not in ignore_type:
            if entity_type in rename_type:
                entity_type = rename_type[entity_type]
            if up_ignore_layer == 1:
                if '-' in entity_type:
                    entity_type = entity_type.split('-')[0]
            elif up_ignore_layer == 2:
                entity_type = "ENTITY"
            filtered_list.append(pair[0]+':'+entity_type)
    return filtered_list



def generate_f_value_report():
    file_list = [
                # "exercise.chenhua.100.ann", 
                "exercise.yangjie.100.ann", 
                "exercise.shaolei.100.ann", 
                "exercise.yuanye.100.ann",
                # "exercise.yanxia.100.ann",
                # "exercise.yuanye.100.ann",
                "exercise.yumin.100.ann"
                # "exercise.hongmin.100.ann",
                # "exercise.yuze.100.ann"
                ]

    file_num = len(file_list)
    result_matrix = np.ones((file_num, file_num))
    result_matrix_ignore_1_layer = np.ones((file_num, file_num))
    result_matrix_ignore_2_layer = np.ones((file_num, file_num))
    for idx in range(file_num-1):
        gold_file = file_list[idx]
        for idy in range(idx+1, file_num):
            pred_file = file_list[idy]
            p,r,f = compare_files(gold_file, pred_file, 0)
            p1,r1,f1 = compare_files(gold_file, pred_file, 1)
            p2,r2,f2 = compare_files(gold_file, pred_file, 2)
            result_matrix[idx][idy] = f
            result_matrix[idy][idx] = f
            result_matrix_ignore_1_layer[idx][idy] = f1
            result_matrix_ignore_1_layer[idy][idx] = f1
            result_matrix_ignore_2_layer[idx][idy] = f2
            result_matrix_ignore_2_layer[idy][idx] = f2
    print 
    ## show final results
    print "FINAL REPORT:  all_catagory/ignore_sub_catogary/entity_chunk"
    print "F1-value".rjust(10),
    for idx in range(file_num):
        print simplified_name(file_list[idx]).rjust(15), 
    print 
    for idx in range(file_num):
        print simplified_name(file_list[idx]).rjust(15), 
        for idy in range(file_num):
            result = output_model(result_matrix[idx][idy], result_matrix_ignore_1_layer[idx][idy], result_matrix_ignore_2_layer[idx][idy])
            print result.rjust(15),
        print


def calculate_average(input_array):
    length = input_array.shape[0]

def output_model(number1, number2):
    if number1 != 'Nan' and number1 != 'nan':
        if number1 == 1.0:
            return " 100/100  "
        else:
            num1 = str(round(number1*100,1))
    else:
        num1 = str(number1)
    if number2 != 'Nan' and number2 != 'nan':
        if number2 == 1.0:
            num2 = "100"
        else:
            num2 = str(round(number2*100,1))
    else:
        num2 = str(number2)
    return num1 + '/'+num2


def number_string(number):
    if number != 'Nan' and number != 'nan':
        return str(round(number*100,2))
    else:
        return str(number)

def p_r_f_string(precison, recall, f):
    return number_string(precison)+'/'+number_string(recall)+'/'+number_string(f)


def simplified_name(file_name):
    name = file_name.split('.')[1]
    return name

def generate_report_from_list(file_list):
    file_num = len(file_list)
    result_matrix = np.ones((file_num, file_num))
    result_matrix_boundary = np.ones((file_num, file_num))
    for idx in range(file_num-1):
        gold_file = file_list[idx]
        for idy in range(idx+1, file_num):
            pred_file = file_list[idy]
            p,r,f = compare_files(gold_file, pred_file, 0)
            p2,r2,f2 = compare_files(gold_file, pred_file, 2)
            result_matrix[idx][idy] = f
            result_matrix[idy][idx] = f
            result_matrix_boundary[idx][idy] = f2
            result_matrix_boundary[idy][idx] = f2
    final_matrix = []

    for idx in range(file_num):
        result_line = []
        for idy in range(file_num):
            result = output_model(result_matrix[idx][idy],  result_matrix_boundary[idx][idy])
            result_line.append(result)
        final_matrix.append(result_line)
    return final_matrix


if __name__ == '__main__':
    gold_file = "sample.gold.ann"
    pred_file = "sample.pred.ann"
    if len(sys.argv) > 2:
        compare_files(sys.argv[1], sys.argv[2])
    else:
        generate_f_value_report()
    






