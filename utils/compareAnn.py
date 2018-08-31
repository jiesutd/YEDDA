# -*- coding: utf-8 -*-
# @Author: Jie
# @Date:   2017-04-25 11:07:00
# @Last Modified by:   Jie Yang,     Contact: jieynlp@gmail.com
# @Last Modified time: 2018-08-30 16:26:39
 

import re
import sys
import numpy as np
from metric4ann import *
import copy

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


def compareBoundary(gold_file, pred_file, out_file):
    # print "Compare files..."
    # print "Gold file:", gold_file
    # print "Pred file:", pred_file
    gold_lines = open(gold_file, 'rU').readlines()
    pred_lines = open(pred_file, 'rU').readlines()
    # out_file = open(output_file,'w')
    sentence_num = len(gold_lines)
    if sentence_num != len(pred_lines):
        return False
    gold_entity = []
    pred_entity = []
    match_entity = []
    start_line = 0
    end_line = sentence_num
    write_head(out_file)
    out_file.write("\\section{Overall Statistics}\n")
    out_file.write("File1 color: "+ "\colorbox{blue!30}{Blue}; Dir: \colorbox{blue!30}{"+gold_file.replace("_", "\_")+"}"+'\\\\'+'\n')
    out_file.write("File2 color: "+"\colorbox{red!30}{Red}; Dir: \colorbox{red!30}{"+pred_file.replace("_", "\_")+"}"+'\\\\'+'\n')
    final_f = compare_f_measure_by_type(gold_file, pred_file)
    # print final_f
    out_file.write("\\begin{table}[!htbp]\n")
    out_file.write("\\centering\n")
    out_file.write("\\caption{Statistics for two annotations, assume File1 as gold standard}\n")
    out_file.write("\\begin{tabular}{l|l|l}\n")
    out_file.write("\\hline\n")
    out_file.write("P/R/F (\%)& Entity &Boundary\\\\\n")
    out_file.write("\\hline\n")
    for idx in range(len(final_f)-2):
        results = final_f[idx].split(':')
        out_file.write(("%s& %s &--\\\\\n")%(results[0], results[1]))
    over_entity = final_f[-2].split(":")[1]
    over_chunk = final_f[-1].split(":")[1]
    out_file.write("\\hline\n")
    out_file.write(("Overall& %s &%s\\\\\n")%(over_entity, over_chunk))
    out_file.write("\\hline\n")
    out_file.write("\\end{tabular}\n")
    out_file.write("\\end{table}\n")
    out_file.write("\\section{Detail Content Comparison}\n")
    out_file.write("\colorbox{blue!30}{Blue}: only annotated in File1.\\\\\n")
    out_file.write("\colorbox{red!30}{Red}: only annotated in File2.\\\\\n")
    out_file.write("\colorbox{green!30}{Green}: annotated in both files.\\\\\n")
    out_file.write("\\rule{5cm}{0.1em}\\\\\n")
    out_file.write("\\vspace{0.3cm}\\\\\n")
    remove_seg = False
    for idx in range(sentence_num):
        if idx >= end_line:
            continue
        if idx < start_line:
            continue
        # print gold_lines[idx]
        gold_enity_list, gold_sentence, gold_bound = get_ner_from_sentence(gold_lines[idx],remove_seg)
        # print "gold:", gold_enity_list
        gold_filter_entity = filter_entity(gold_enity_list, 2)
        # print "gold:", gold_filter_entity
        pred_entity_list, pred_sentence, pred_bound = get_ner_from_sentence(pred_lines[idx],remove_seg)
        pred_filter_entity = filter_entity(pred_entity_list, 2)
        # print "pred:",pred_filter_entity
        out_latex = generate_latex(gold_sentence, gold_bound, pred_bound)
        # out_latex = generate_specific_latex(gold_sentence, gold_enity_list, pred_entity_list).encode('utf-8')å
        out_file.write(out_latex+'\\\\'+'\n')
    write_end(out_file)
    
    return True

## generate specific latex code for each sentence
def generate_specific_latex(sentence, gold_entity_list, pred_entity_list):
    print "".join(sentence)
    final_segment = generate_specific_segment(sentence, gold_entity_list, pred_entity_list)
    segment_dict = {}
    for segment in final_segment:
        start_pos = int(segment.split(',')[0].split('[')[1])
        if start_pos not in segment_dict:
            segment_dict[start_pos] = segment
    sorted_segment = []
    for key in sorted(segment_dict.iterkeys()):
        sorted_segment.append(segment_dict[key])
    output_string = ""
    for segment in sorted_segment:
        output_string += generate_segment_latex(sentence, segment)
    return output_string



def generate_segment_latex(sentence, segment):
    segment_type = segment[0]
    if segment_type == "M":
        return generate_match(sentence, segment)
    elif segment_type == "O":
        return generate_overlap(sentence,segment)
    elif segment_type == "G":
        return generate_gold_left(sentence,segment)
    elif segment_type == "P":
        return generate_pred_left(sentence,segment)
    else:
        return generate_not_entity(sentence,segment)


def generate_overlap(sentence, match_segment):
    output_string = "\colorbox{yellow!70}{$"
    gold = match_segment.split('_')[1]
    pred = match_segment.split('_')[2]

    gold_pos = gold.split(":")[0].strip("G[]").split(',')
    gold_start = int(gold_pos[0])
    gold_end = int(gold_pos[1])
    gold_type = gold.split(":")[1]

    pred_pos = pred.split(":")[0].strip("P[]").split(',')
    pred_type = pred.split(":")[1]
    pred_start = int(pred_pos[0])
    pred_end = int(pred_pos[1])
    overlap_start = -1
    overlap_end = -1
    if gold_start < pred_start:
        front_words = "".join(sentence[gold_start:pred_start])
        front_flag = "G"
        overlap_start = pred_start
    elif gold_start > pred_start:
        front_words = "".join(sentence[pred_start:gold_start])
        front_flag = "P"
        overlap_start = gold_start
    else:
        front_words = ""
        front_flag = "O"
        overlap_start = gold_start

    if gold_end < pred_end:
        back_words = "".join(sentence[gold_start:pred_start])
        back_flag = "P"
        overlap_end = gold_end
    elif gold_end > pred_end:
        back_words = "".join(sentence[pred_start:gold_start])
        back_flag = "G"
        overlap_end = pred_end
    else:
        back_words = ""
        back_flag = "O"
        overlap_end = gold_end
    overlap_words = "".join(sentence[overlap_start:overlap_end])
    if front_words:
        if front_flag == "P":
            output_string += "\underline{\\text{"+ front_words + "}}"
        else:
            output_string += "\overline{\\text{"+ front_words + "}}"
    output_string += "\overline{\underline{\\text{"+ overlap_words + "}}}"
    if back_words:
        if back_flag == "P":
            output_string += "\underline{\\text{"+ back_words + "}}"
        else:
            output_string += "\overline{\\text{"+ back_words + "}}"
    output_string += "$}$^{{\color{blue}{"+gold_type+"}}}_{{\color{red}{"+pred_type+"}}}$"

    return output_string


def generate_match(sentence, match_segment):
    output_string = ""
    entity_type = match_segment.split(':')[1]
    pos = match_segment.split(':')[0].strip('M[]').split(',')
    start = int(pos[0])
    end = int(pos[1])
    words = sentence[start:end+1]
    output_string = "\colorbox{green!30}{$\underline{\overline{\\text{" +''.join(words)+"}}}$}$^{{\color{blue}{"+entity_type+"}}}_{{\color{red}{"+entity_type+"}}}$"
    return output_string

def generate_not_entity(sentence, match_segment):
    output_string = ""
    pos = match_segment.split(':')[0].strip('N[]').split(',')
    start = int(pos[0])
    end = int(pos[1])
    words = sentence[start:end+1]
    output_string = ''.join(words)
    return output_string

def generate_gold_left(sentence, match_segment):
    output_string = ""
    entity_type = match_segment.split(':')[1]
    pos = match_segment.split(':')[0].strip('G[]').split(',')
    start = int(pos[0])
    end = int(pos[1])
    words = sentence[start:end+1]
    output_string = "\colorbox{blue!30}{$\overline{\\text{" +''.join(words)+"}}$}$^{{\color{blue}{"+entity_type+"}}}"
    return output_string

def generate_pred_left(sentence, match_segment):
    output_string = ""
    entity_type = match_segment.split(':')[1]
    pos = match_segment.split(':')[0].strip('P[]').split(',')
    start = int(pos[0])
    end = int(pos[1])
    words = sentence[start:end+1]
    output_string = "\colorbox{red!30}{$\underline{\\text{" +''.join(words)+"}}$}$_{{\color{red}{"+entity_type+"}}}$"
    return output_string


def generate_specific_segment(sentence, gold_entity_list, pred_entity_list):
    sent_length = len(sentence)
    matched_entity = []
    gold_left = []
    pred_left = []
    for entity in gold_entity_list:
        if entity in pred_entity_list:
            matched_entity.append("M"+entity)
        else:
            gold_left.append(entity)
    for entity in pred_entity_list:
        if entity not in gold_entity_list:
            pred_left.append(entity)
    print "match:",matched_entity
    overlaped_entity = []
    gold_overlaped = []
    pred_overlaped = []
    for gold_entity in gold_left:
        gold_removed = False
        for pred_entity in pred_left:
            if not gold_removed:
                overlaped = entity_overlap_span(gold_entity, pred_entity)
                if overlaped != -1:
                    overlaped_entity.append(overlaped)
                    gold_overlaped.append(gold_entity)
                    if pred_entity not in pred_overlaped:
                        pred_overlaped.append(pred_entity)
                    gold_removed = True
                else:
                    pass
    for entity in gold_overlaped:
        gold_left.remove(entity)
    for entity in pred_overlaped:
        pred_left.remove(entity)
    print "overlap:",overlaped_entity
    new_gold_left = []
    new_pred_left = []
    for entity in gold_left:
        new_gold_left.append('G'+entity)
    for entity in pred_left:
        new_pred_left.append('P'+entity)

    print "final gold:",new_gold_left
    print "final pred:",new_pred_left
    final_segment = matched_entity + overlaped_entity + new_gold_left + new_pred_left
    matched_flag = [0]*sent_length
    for entity in final_segment:
        pos = entity.split('_')[0].split(':')[0].strip(']').split(',')
        entity_type = pos[0].split('[')[0]
        start = int(pos[0].split('[')[1])
        end = int(pos[1])
        for idy in range(start, end+1):
            if entity_type == "M":
                matched_flag[idy] = 1
            elif entity_type == "O":
                matched_flag[idy] = 2
            elif entity_type == "G":
                matched_flag[idy] = 3
            elif entity_type == "P":
                matched_flag[idy] = 4
    start = -1
    for idx in range(sent_length):
        if matched_flag[idx] == 0:
            if start == -1:
                start = idx
        else:
            if start != -1:
                final_segment.append("N["+str(start)+","+str(idx-1)+"]")
                start = -1
    print "final",final_segment
    print
    # print "match:",generate_match(sentence,matched_entity[0])
    # print "overlap:",generate_overlap(sentence,overlaped_entity[0])
    # print "no entity:",generate_not_entity(sentence,final_segment[-1])
    # if new_gold_left:
    #     print "gold left:",generate_gold_left(sentence,new_gold_left[0])
    # if new_pred_left:
    #     print "pred left:",generate_pred_left(sentence,new_pred_left[0])

    # exit(0)
    return final_segment








def entity_overlap_span(gold_entity, pred_entity):
    gold_type = gold_entity.split(':')[1]
    gold_pos = gold_entity.split(':')[0].strip('[]').split(',')
    gold_start = int(gold_pos[0])
    gold_end = int(gold_pos[1])
    pred_type = pred_entity.split(':')[1]
    pred_pos = pred_entity.split(':')[0].strip('[]').split(',')
    pred_start = int(pred_pos[0])
    pred_end = int(pred_pos[1])
    gold_set = set([gold_start, gold_end])
    pred_set = set([pred_start, pred_end])
    if gold_set.intersection(pred_set):
        start = min(gold_start,pred_start)
        end = max(gold_end,pred_end)
        return "O["+str(start)+","+ str(end)+"]_G["+str(gold_start)+ ","+str(gold_end)+"]:"+gold_type + "_P["+str(pred_start)+ ","+str(pred_end)+"]:"+pred_type
    else:
        return -1



def generate_latex(sentence, gold_bound, pred_bound):
    sent_length = len(sentence)
    word_chunk = []
    color_chunk = []
    word_segment = ''
    segment_tag = -2
    output_string = ''
    for idx in range(sent_length):
        word = sentence[idx].encode('utf-8')
        if gold_bound[idx] == 1:
            if pred_bound[idx] == 1:
                if segment_tag == 2:
                    word_segment += word
                else:
                    if segment_tag != -2:
                        word_chunk.append(word_segment)
                        color_chunk.append(segment_tag)
                    segment_tag = 2
                    word_segment = word
                    # print "segment 2:", word_segment
            else:
                if segment_tag == 1:
                    word_segment += word
                else:
                    if segment_tag != -2:
                        word_chunk.append(word_segment)
                        color_chunk.append(segment_tag)
                    segment_tag = 1
                    word_segment = word
                    # print "segment 1:", word_segment
        else:
            # print "".join(sentence)
            # print gold_bound
            # print pred_bound
            # print len(pred_bound),len(gold_bound), len(sentence), idx
            if pred_bound[idx] == 1:
                if segment_tag == -1:
                    word_segment += word
                else:
                    if segment_tag != -2:
                        word_chunk.append(word_segment)
                        color_chunk.append(segment_tag)
                    segment_tag = -1
                    word_segment = word
                    # print "segment -1:", word_segment
            else:
                if segment_tag == 0:
                    word_segment += word
                else:
                    if segment_tag != -2:
                        word_chunk.append(word_segment)
                        color_chunk.append(segment_tag)
                    segment_tag = 0
                    word_segment = word
                    # print "segment 0:", word_segment
    if segment_tag != -2:
        word_chunk.append(word_segment)
        color_chunk.append(segment_tag)

    for idx in range(len(word_chunk)):
        # print word_chunk[idx], color_chunk[idx]
        if color_chunk[idx] == 2:
            output_string += "\colorbox{green!30}{" + word_chunk[idx] + '}'
        elif color_chunk[idx] == 1:
            output_string += "\colorbox{blue!30}{" + word_chunk[idx] + '}'
        elif color_chunk[idx] == 0:
            output_string += word_chunk[idx]
        elif color_chunk[idx] == -1:
            output_string += "\colorbox{red!30}{" + word_chunk[idx] + '}'

    if "%" in  output_string:
        output_string = output_string.replace("%", "\%")
    return output_string



def get_ner_from_sentence(sentence, remove_seg=True):
    ## remove segmentation space, avoid segmentation changes
    if remove_seg:
        sentence = sentence.strip().replace(' ', '').decode('utf-8')
    else:
        sentence = sentence.strip().decode('utf-8')
    sentence_len = len(sentence)
    # print sentence
    entity_start = []
    words = []
    words_bound = []
    last_char = ''
    entity_type_start = False
    entity_type = ''
    word_id = 0
    entity_list = []
    origin_text = ""
    for idx in range(sentence_len):
        if sentence[idx] == '[':
            left_bracket = True 
        elif sentence[idx] == '@' or sentence[idx] == '$':
            if last_char == '[':
                entity_start.append(word_id)
            else:
                words.append(sentence[idx])
                word_id += 1
                words_bound.append(0)
        elif sentence[idx] == '#':
            if len(entity_start) > 0:
                entity_type_start = True
            else:
                words.append(sentence[idx])
                word_id += 1
                words_bound.append(0)
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
                    words_bound.append(0)
        else:
            if entity_type_start:
                entity_type += sentence[idx]
            else:
                words.append(sentence[idx])
                word_id += 1
                if entity_start:
                    words_bound.append(1)
                else:
                    words_bound.append(0)

        last_char = sentence[idx]
    assert(len(words)==len(words_bound))
    # print entity_list
    # for idx in range(len(words)):
    #     print words[idx],'/',words_bound[idx], " ",

    return entity_list, words, words_bound
    # print entity_list
    



def calculate_average(input_array):
    length = input_array.shape[0]




def write_head(out_file):
    out_file.write("%%%%%%%%%%%%%%%%%%%%%%% file typeinst.tex %%%%%%%%%%%%%%%%%%%%%%%%%\n")
    out_file.write("\documentclass[runningheads,a4paper]{llncs}\n")
    out_file.write("\usepackage{amssymb}\n")
    out_file.write("\setcounter{tocdepth}{3}\n")
    out_file.write("\usepackage{graphicx}\n")
    out_file.write("\usepackage{multirow}\n")
    out_file.write("\usepackage{subfigure}\n")
    out_file.write("\usepackage{amsmath}\n")
    out_file.write("\usepackage{CJK}\n")
    out_file.write("\usepackage{color}\n")
    out_file.write("\usepackage{xcolor}\n")
    out_file.write("\usepackage{url}\n")
    out_file.write("\\begin{document}\n")
    out_file.write("\\begin{CJK*}{UTF8}{gbsn}\n")
    out_file.write("\mainmatter  % start of an individual contribution\n")
    out_file.write("\\title{Annotation Comparison Report}\n")
    out_file.write("\\author{SUTDNLP Group}\n")
    out_file.write("\\institute{Singapore University of Technology and Design}\n")
    
    out_file.write("\\maketitle\n\n")



def write_end(out_file):
    out_file.write("\end{CJK*}\n")
    out_file.write("\end{document}\n")
    


def simplified_name(file_name):
    name = file_name.split('.')[1]
    return name

if __name__ == '__main__':
    gold_file = "../../Linwei/NER_Labeling1.txt.ann"
    pred_file = "../../Xingxuan/NER_Labeling2.txt.ann"
    output_file = open("../tex2pdf/test.tex",'w')

    compareBoundary(gold_file,pred_file,output_file)
    output_file.close()
    # demo_sentence = "这 方面 需 考虑 到 维稳 汇率 、 [@美联储#Org-Government*] 加息 进程 的 掣肘 , 以及 抑制 资产 泡沫 和 防范 经济 金融 风险 等 因素 。 "

    






