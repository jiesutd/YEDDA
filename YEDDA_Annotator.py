# -*- coding: utf-8 -*-
# @Author: Jie Yang from SUTD
# @Date:   2016-Jan-06 17:11:59
# @Last Modified by:   Jie Yang,     Contact: jieynlp@gmail.com
# @Last Modified time: 2018-07-15 20:33:40
# !/usr/bin/env python
# coding=utf-8

from Tkinter import *
from ttk import *  # Frame, Button, Label, Style, Scrollbar
import tkFileDialog
import tkFont
import json
from collections import deque
import pickle
import os.path
import platform
from utils.recommend import *
import tkMessageBox


class Example(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.Version = "YEDDA-V1.0 Annotator"
        self.OS = platform.system().lower()
        self.parent = parent
        self.fileName = ""
        self.debug = False
        self.colorAllChunk = True
        self.recommendFlag = True
        self.history = deque(maxlen=20)
        self.currentContent = deque(maxlen=1)
        self.pressCommand = {'a': "Artificial",
                             'b': "Event",
                             'c': "Fin-Concept",
                             'd': "Location",
                             'e': "Organization",
                             'f': "Person",
                             'g': "Sector",
                             'h': "Other"
                             }
        self.allKey = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.controlCommand = {'q': "unTag", 'ctrl+z': 'undo'}
        self.labelEntryList = []
        self.shortcutLabelList = []
        # default GUI display parameter
        if len(self.pressCommand) > 20:
            self.textRow = len(self.pressCommand)
        else:
            self.textRow = 20
        self.textColumn = 5
        self.questionHeight = 4
        self.questionWidth = 50
        self.answerHeight = 3
        self.answerWidth = 50
        self.tagScheme = "BMES"
        self.onlyNP = False  # for exporting sequence
        self.keepRecommend = True

        self.seged = True  # False for non-segmentated Chinese, True for English or Segmented Chinese
        self.configFile = "config"
        self.entityRe = r'\[\@.*?\@\]'
        self.insideNestEntityRe = r'\[\@\[\@(?!\[\@).*?\#.*?\*\]\#'
        self.recommendRe = r'\[\$.*?\#.*?\*\](?!\#)'
        self.goldAndrecomRe = r'\[\@.*?\#.*?\*\](?!\#)'
        if self.keepRecommend:
            self.goldAndrecomRe = r'\[[\@\$)].*?\#.*?\*\](?!\#)'
        self.entityColor = "SkyBlue1"
        self.insideNestEntityColor = "light slate blue"
        self.recommendColor = 'lightgreen'
        self.selectColor = 'light salmon'
        self.textFontStyle = "Times"
        self.currentQuestionID = 0    #  the id of question that is currently presented
        self.currentBeginningAnswerID = 0
        self.currentTextQuestionBrief = {}
        self.keyPhraseDict = {}  #  key:questionID, value: set of keyphrases
        self.initUI()

    def initUI(self):
        self.parent.title(self.Version)
        self.pack(fill=BOTH, expand=True)

        self.lbl = Label(self, text="File: no file is opened")
        self.lbl.grid(sticky=W)

        self.fnt = tkFont.Font(family=self.textFontStyle, size=self.textRow,weight="bold", underline=0)

        self.questionLabel = Label(self, text="Question:")
        self.questionLabel.grid(row=1, sticky=W)

        self.question = Text(self, font=self.fnt, selectbackground=self.selectColor,  height=self.questionHeight,
                             width=self.questionWidth)
        self.question.grid(row=2, columnspan=self.textColumn, sticky=E+W+S+N)

        self.sbQuestion = Scrollbar(self)
        self.sbQuestion.grid(row=2, column=self.textColumn, rowspan=self.questionHeight, sticky=E+W+S+N)
        self.question['yscrollcommand'] = self.sbQuestion.set
        self.sbQuestion['command'] = self.question.yview

        self.answer1Label = Label(self, text="Answer 1:")
        self.answer1Label.grid(row=6, sticky=W)

        self.answerText1 = Text(self, font=self.fnt, selectbackground=self.selectColor, height=self.answerHeight,
                                width=self.answerWidth)
        self.answerText1.grid(row=7, columnspan=self.textColumn, sticky=E+W+S+N)

        self.sbAnswer1 = Scrollbar(self)
        self.sbAnswer1.grid(row=7, column=self.textColumn, rowspan=self.answerHeight, padx=0, sticky=E+W+S+N)
        self.answerText1['yscrollcommand'] = self.sbAnswer1.set
        self.sbAnswer1['command'] = self.answerText1.yview

        self.answer2Label = Label(self, text="Answer 2:")
        self.answer2Label.grid(row=10, sticky=W)

        self.answerText2 = Text(self, font=self.fnt, selectbackground=self.selectColor, height=self.answerHeight,
                                width=self.answerWidth)
        self.answerText2.grid(row=11, columnspan=self.textColumn, sticky=E+W+S+N)

        self.sbAnswer2 = Scrollbar(self)
        self.sbAnswer2.grid(row=11, column=self.textColumn, rowspan=self.answerHeight, padx=0, sticky=E+W+S+N)
        self.answerText2['yscrollcommand'] = self.sbAnswer2.set
        self.sbAnswer2['command'] = self.answerText2.yview

        self.answer3Label = Label(self, text="Answer 3:")
        self.answer3Label.grid(row=14, sticky=W)

        self.answerText3 = Text(self, font=self.fnt, selectbackground=self.selectColor, height=self.answerHeight,
                                width=self.answerWidth)
        self.answerText3.grid(row=15, columnspan=self.textColumn, sticky=E+W+S+N)

        self.sbAnswer3 = Scrollbar(self)
        self.sbAnswer3.grid(row=15, column=self.textColumn, rowspan=self.answerHeight, padx=0, sticky=E+W+S+N)
        self.answerText3['yscrollcommand'] = self.sbAnswer3.set
        self.sbAnswer3['command'] = self.answerText3.yview

        self.answer4Label = Label(self, text="Answer 4:")
        self.answer4Label.grid(row=18, sticky=W)

        self.answerText4 = Text(self, font=self.fnt, selectbackground=self.selectColor, height=self.answerHeight,
                                width=self.answerWidth)
        self.answerText4.grid(row=19, columnspan=self.textColumn, sticky=E+W+S+N)

        self.sbAnswer4 = Scrollbar(self)
        self.sbAnswer4.grid(row=19, column=self.textColumn, rowspan=self.answerHeight, padx=0, sticky=E+W+S+N)
        self.answerText4['yscrollcommand'] = self.sbAnswer4.set
        self.sbAnswer4['command'] = self.answerText4.yview

        self.answer5Label = Label(self, text="Answer 5:")
        self.answer5Label.grid(row=22, sticky=W)

        self.answerText5 = Text(self, font=self.fnt, selectbackground=self.selectColor, height=self.answerHeight,
                                width=self.answerWidth)
        self.answerText5.grid(row=23, columnspan=self.textColumn, sticky=E+W+S+N)

        self.sbAnswer5 = Scrollbar(self)
        self.sbAnswer5.grid(row=23, column=self.textColumn, rowspan=self.answerHeight, padx=0, sticky=E+W+S+N)
        self.answerText5['yscrollcommand'] = self.sbAnswer5.set
        self.sbAnswer5['command'] = self.answerText5.yview

        nextButton = Button(self, text="Next", command=self.nextPage)
        nextButton.grid(row=26, column=self.textColumn)

        backButton = Button(self, text="Back", command=self.prevPage)
        backButton.grid(row=26, column=self.textColumn - 1)

        abtn = Button(self, text="Open", command=self.onOpen)
        abtn.grid(row=26, column=self.textColumn - 2)

        nextQuestionBtn = Button(self, text="NextQuestion", command=self.nextQuestion)
        nextQuestionBtn.grid(row=26, column=self.textColumn - 3)

        prevQuestionBtn = Button(self, text="PrevQuestion", command=self.prevQuestion)
        prevQuestionBtn.grid(row=26, column=self.textColumn - 4)

        exportBtn = Button(self, text="Export", command=self.exportToJSON)
        exportBtn.grid(row=26, column=self.textColumn - 5)

        for idx in range(0, len(self.allKey)):
            press_key = self.allKey[idx]
            self.answerText1.bind(press_key, self.answer1ReturnEnter)
            self.answerText2.bind(press_key, self.answer2ReturnEnter)
            self.answerText3.bind(press_key, self.answer3ReturnEnter)
            self.answerText4.bind(press_key, self.answer4ReturnEnter)
            self.answerText5.bind(press_key, self.answer5ReturnEnter)
            simplePressKey = " <KeyRelease-" + press_key + ">"
            self.answerText1.bind(simplePressKey, self.deleteText1Input)
            self.answerText2.bind(simplePressKey, self.deleteText2Input)
            self.answerText3.bind(simplePressKey, self.deleteText3Input)
            self.answerText4.bind(simplePressKey, self.deleteText4Input)
            self.answerText5.bind(simplePressKey, self.deleteText5Input)


        self.presentTextLabel = Label(self, text="Label Result:")
        self.presentTextLabel.grid(row=1, column=self.textColumn+1)
        self.presentText = Text(self, font=self.fnt, selectbackground=self.selectColor, height=self.questionHeight,
                               width=self.answerWidth - 25)
        self.presentText.grid(row=2, column=self.textColumn+1, sticky=E+W+S+N)
        self.sbPresentText = Scrollbar(self)
        self.sbPresentText.grid(row=2, column=self.textColumn+ 1 + self.answerWidth - 25, rowspan=self.answerHeight, sticky=W+E+S+N)
        self.presentText['yscrollcommand'] = self.sbPresentText.set
        self.sbPresentText['command'] = self.presentText.yview

    def exportToJSON(self):
        exportObj = []
        for questionID in self.keyPhraseDict:
            dict = {}
            dict["Title"] = self.form_json[questionID]["Title"]
            dict["IsShortTextQuestion"] = self.form_json[questionID]["IsShortTextQuestion"]
            dict["KeyPhrases"] = list(self.keyPhraseDict[questionID])
            exportObj.append(dict)

        newContent = json.dumps(exportObj)

        new_name = self.fileName + '_labeling.json'
        label_file = open(new_name, 'w')
        label_file.write(newContent)
        label_file.close()

    def prevPage(self):
        responseList = self.currentTextQuestionBrief["Responses"]
        if (self.currentBeginningAnswerID - 5 >= 0):
            self.currentBeginningAnswerID = self.currentBeginningAnswerID - 5
        if (self.currentBeginningAnswerID >= 0):
            reachBeginning = False
        else:
            reachBeginning = True
        if (reachBeginning is False):
            for i in range(0, 5):
                currentAnswerID = self.currentBeginningAnswerID + i
                if currentAnswerID < len(responseList):
                    if i == 0:
                        self.answerText1.delete("1.0", END)
                        self.answerText1.insert(END, responseList[currentAnswerID])
                    if i == 1:
                        self.answerText2.delete("1.0", END)
                        self.answerText2.insert(END, responseList[currentAnswerID])
                    if i == 2:
                        self.answerText3.delete("1.0", END)
                        self.answerText3.insert(END, responseList[currentAnswerID])
                    if i == 3:
                        self.answerText4.delete("1.0", END)
                        self.answerText4.insert(END, responseList[currentAnswerID])
                    if i == 4:
                        self.answerText5.delete("1.0", END)
                        self.answerText5.insert(END, responseList[currentAnswerID])
                else:
                    break

    ##  cursor index show with the left click
    def nextPage(self):
        responseList = self.currentTextQuestionBrief["Responses"]
        if (self.currentBeginningAnswerID  + 5 < len(responseList)):
            self.currentBeginningAnswerID = self.currentBeginningAnswerID + 5
        if (self.currentBeginningAnswerID < len(responseList)):
            reachEnd = False
        else:
            reachEnd = True
        for i in range(0, 5):
            currentAnswerID = self.currentBeginningAnswerID + i
            if currentAnswerID < len(responseList):
                if i == 0:
                    self.answerText1.delete("1.0", END)
                    self.answerText1.insert(END, responseList[currentAnswerID])
                if i == 1:
                    self.answerText2.delete("1.0", END)
                    self.answerText2.insert(END, responseList[currentAnswerID])
                if i == 2:
                    self.answerText3.delete("1.0", END)
                    self.answerText3.insert(END, responseList[currentAnswerID])
                if i == 3:
                    self.answerText4.delete("1.0", END)
                    self.answerText4.insert(END, responseList[currentAnswerID])
                if i == 4:
                    self.answerText5.delete("1.0", END)
                    self.answerText5.insert(END, responseList[currentAnswerID])
            elif reachEnd is False:
                if i == 0:
                    self.answerText1.delete("1.0", END)
                if i == 1:
                    self.answerText2.delete("1.0", END)
                if i == 2:
                    self.answerText3.delete("1.0", END)
                if i == 3:
                    self.answerText4.delete("1.0", END)
                if i == 4:
                    self.answerText5.delete("1.0", END)
            else:
                break

    ##  cursor index show with the left click
    def singleLeftClick(self, event):
        if self.debug:
            print "Action Track: singleLeftClick"
        cursor_index = self.text.index(INSERT) 
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s\ncol: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)

    ## TODO: select entity by double left click
    def doubleLeftClick(self, event):
        if self.debug:
            print "Action Track: doubleLeftClick"
        pass
        # cursor_index = self.text.index(INSERT)
        # start_index = ("%s - %sc" % (cursor_index, 5))
        # end_index = ("%s + %sc" % (cursor_index, 5))
        # self.text.tag_add('SEL', '1.0',"end-1c")

    ## Disable right click default copy selection behaviour
    def rightClick(self, event):
        if self.debug:
            print "Action Track: rightClick"
        try:
            firstSelection_index = self.text.index(SEL_FIRST)
            cursor_index = self.text.index(SEL_LAST)
            content = self.text.get('1.0',"end-1c").encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            pass

    def setInRecommendModel(self):
        self.recommendFlag = True
        self.RecommendModelFlag.config(text = str(self.recommendFlag))
        tkMessageBox.showinfo("Recommend Model", "Recommend Model has been activated!")

    def setInNotRecommendModel(self):
        self.recommendFlag = False 
        self.RecommendModelFlag.config(text = str(self.recommendFlag))
        content = self.getText()
        content = removeRecommendContent(content,self.recommendRe)
        self.writeFile(self.fileName, content, '1.0')
        tkMessageBox.showinfo("Recommend Model", "Recommend Model has been deactivated!")

    def onOpen(self):
        ftypes = [('json files', '.json')]
        dlg = tkFileDialog.Open(self, filetypes=ftypes)
        fl = dlg.show()
        if fl != '':
            text = self.readFile(fl)
            self.setNameLabel("File: " + fl)
            self.form_json = json.loads(text)

            if self.form_json:
                for i in range(0, len(self.form_json)):
                    self.keyPhraseDict[i] = set()
                self.currentTextQuestionBrief = self.form_json[0]
                questionText = self.currentTextQuestionBrief["Title"]
                self.question.delete("1.0", END)
                self.question.insert(END, questionText)
                responseList = self.currentTextQuestionBrief["Responses"]
                for i in range(0, 5):
                    currentAnswerID = self.currentBeginningAnswerID + i
                    if currentAnswerID < len(responseList):
                        if i == 0:
                            self.answerText1.delete("1.0", END)
                            self.answerText1.insert(END, responseList[currentAnswerID])
                        if i == 1:
                            self.answerText2.delete("1.0", END)
                            self.answerText2.insert(END, responseList[currentAnswerID])
                        if i == 2:
                            self.answerText3.delete("1.0", END)
                            self.answerText3.insert(END, responseList[currentAnswerID])
                        if i == 3:
                            self.answerText4.delete("1.0", END)
                            self.answerText4.insert(END, responseList[currentAnswerID])
                        if i == 4:
                            self.answerText5.delete("1.0", END)
                            self.answerText5.insert(END, responseList[currentAnswerID])
                    else:
                        break

    def prevQuestion(self):
        if self.form_json:
            if (self.currentQuestionID - 1 >= 0):
                self.currentQuestionID = self.currentQuestionID - 1
            self.showLabeledKeyPhrase()
            self.currentBeginningAnswerID = 0
            self.currentTextQuestionBrief = self.form_json[self.currentQuestionID]
            questionText = self.currentTextQuestionBrief["Title"]
            self.question.delete("1.0", END)
            self.question.insert(END, questionText)
            responseList = self.currentTextQuestionBrief["Responses"]
            for i in range(0, 5):
                currentAnswerID = self.currentBeginningAnswerID + i
                if currentAnswerID < len(responseList):
                    if i == 0:
                        self.answerText1.delete("1.0", END)
                        self.answerText1.insert(END, responseList[currentAnswerID])
                    if i == 1:
                        self.answerText2.delete("1.0", END)
                        self.answerText2.insert(END, responseList[currentAnswerID])
                    if i == 2:
                        self.answerText3.delete("1.0", END)
                        self.answerText3.insert(END, responseList[currentAnswerID])
                    if i == 3:
                        self.answerText4.delete("1.0", END)
                        self.answerText4.insert(END, responseList[currentAnswerID])
                    if i == 4:
                        self.answerText5.delete("1.0", END)
                        self.answerText5.insert(END, responseList[currentAnswerID])
                else:
                    break


    def nextQuestion(self):
        if self.form_json:
            if (self.currentQuestionID + 1 < len(self.form_json)):
                self.currentQuestionID = self.currentQuestionID + 1
            self.showLabeledKeyPhrase()
            self.currentBeginningAnswerID = 0
            self.currentTextQuestionBrief = self.form_json[self.currentQuestionID]
            questionText = self.currentTextQuestionBrief["Title"]
            self.question.delete("1.0", END)
            self.question.insert(END, questionText)
            responseList = self.currentTextQuestionBrief["Responses"]
            for i in range(0, 5):
                currentAnswerID = self.currentBeginningAnswerID + i
                if currentAnswerID < len(responseList):
                    if i == 0:
                        self.answerText1.delete("1.0", END)
                        self.answerText1.insert(END, responseList[currentAnswerID])
                    if i == 1:
                        self.answerText2.delete("1.0", END)
                        self.answerText2.insert(END, responseList[currentAnswerID])
                    if i == 2:
                        self.answerText3.delete("1.0", END)
                        self.answerText3.insert(END, responseList[currentAnswerID])
                    if i == 3:
                        self.answerText4.delete("1.0", END)
                        self.answerText4.insert(END, responseList[currentAnswerID])
                    if i == 4:
                        self.answerText5.delete("1.0", END)
                        self.answerText5.insert(END, responseList[currentAnswerID])
                else:
                    break

    def readFile(self, filename):
        f = open(filename, "rU")
        text = f.read()
        self.fileName = filename
        return text

    def setFont(self, value):
        _family=self.textFontStyle
        _size = value
        _weight="bold"
        _underline=0
        fnt = tkFont.Font(family= _family,size= _size,weight= _weight,underline= _underline)
        Text(self, font=fnt)
    
    def setNameLabel(self, new_file):
        self.lbl.config(text=new_file)

    def setCursorLabel(self, cursor_index):
        if self.debug:
            print "Action Track: setCursorLabel"
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s\ncol: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)


    def returnEnter(self,event):
        if self.debug:
            print "Action Track: returnEnter"
        self.pushToHistory()
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content


    def answer1ReturnEnter(self,event):
        press_key = event.char
        print "event: ", press_key
        self.executeCursorCommand(press_key.lower(), self.answerText1, 0)
        return press_key

    def answer2ReturnEnter(self,event):
        press_key = event.char
        print "event: ", press_key
        self.executeCursorCommand(press_key.lower(), self.answerText2, 1)
        return press_key

    def answer3ReturnEnter(self,event):
        press_key = event.char
        print "event: ", press_key
        self.executeCursorCommand(press_key.lower(), self.answerText3, 2)
        return press_key

    def answer4ReturnEnter(self,event):
        press_key = event.char
        print "event: ", press_key
        self.executeCursorCommand(press_key.lower(), self.answerText4, 3)
        return press_key

    def answer5ReturnEnter(self,event):
        press_key = event.char
        print "event: ", press_key
        self.executeCursorCommand(press_key.lower(), self.answerText5, 4)
        return press_key

    def backToHistory(self,event):
        if self.debug:
            print "Action Track: backToHistory"
        if len(self.history) > 0:
            historyCondition = self.history.pop()
            # print "history condition: ", historyCondition
            historyContent = historyCondition[0]
            # print "history content: ", historyContent
            cursorIndex = historyCondition[1]
            # print "get history cursor: ", cursorIndex
            self.writeFile(self.fileName, historyContent, cursorIndex)
        else:
            print "History is empty!"
        self.text.insert(INSERT, 'p')   # add a word as pad for key release delete

    def keepCurrent(self, event):
        if self.debug:
            print "Action Track: keepCurrent"
        print("keep current, insert:%s"%(INSERT))
        print "before:", self.text.index(INSERT)
        self.text.insert(INSERT, 'p')
        print "after:", self.text.index(INSERT)

    def clearCommand(self):
        if self.debug:
            print "Action Track: clearCommand"
        self.entry.delete(0, 'end')

    def getText(self):
        textContent = self.text.get("1.0","end-1c")
        textContent = textContent.encode('utf-8')
        return textContent

    ## TODO
    def showLabeledKeyPhrase(self):
        #this is the keyPhrase set for the question id
        set = self.keyPhraseDict[self.currentQuestionID]
        string = ''
        for keyphrase in set:
            ## insert each key phrase into the text widget
            string = string + keyphrase
            string = string + '\n'
        self.presentText.delete("1.0", END)
        self.presentText.insert(END, string)

    #press a key

    def executeCursorCommand(self, command, textWidget, index):
        #content = self.getText()
        print("Command:"+command)
        firstSelection_index = textWidget.index(SEL_FIRST)
        cursor_index = textWidget.index(SEL_LAST)

        aboveHalf_content = textWidget.get('1.0', firstSelection_index)   #text before selected text
        followHalf_content = textWidget.get(firstSelection_index, "end-1c")   #text begin at selected text
        selected_string = textWidget.selection_get()
        #if the selcted string has not been labeled
        if re.match(self.entityRe, selected_string) != None :
            ## if have selected entity
            new_string = selected_string.strip('[@@]')
            followHalf_content = followHalf_content.replace(selected_string, new_string, 1)
            selected_string = new_string
            cursor_index = cursor_index.split('.')[0]+"."+str(int(cursor_index.split('.')[1])-4)
        afterEntity_content = followHalf_content[len(selected_string):]

        if self.currentQuestionID not in self.keyPhraseDict:
            self.keyPhraseDict[self.currentQuestionID] = set()

        self.keyPhraseDict[self.currentQuestionID].add(selected_string.strip())
        self.showLabeledKeyPhrase()
        if command == "q":
            print 'q: remove entity label'
        else:
            if len(selected_string) > 0:
                entity_content, cursor_index = self.replaceString(selected_string, selected_string, cursor_index)
        aboveHalf_content += entity_content #first half content plus selected text with framework
        #content = self.addRecommendContent(aboveHalf_content, afterEntity_content, self.recommendFlag)
        ##  TODO
        content = aboveHalf_content + afterEntity_content
        content = content.encode('utf-8')
        self.writeFile(self.fileName, content, index)

    def deleteText1Input(self,event):
        if self.debug:
            print "Action Track: deleteTextInput"
        get_insert = self.answerText1.index(INSERT)
        print "delete insert:", get_insert
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1])-1)
        get_input = self.answerText1.get(last_insert, get_insert).encode('utf-8')
        # print "get_input: ", get_input
        aboveHalf_content = self.answerText1.get('1.0', last_insert).encode('utf-8')
        followHalf_content = self.answerText1.get(last_insert, "end-1c").encode('utf-8')
        if len(get_input) > 0: 
            followHalf_content = followHalf_content.replace(get_input, '', 1)
        content = aboveHalf_content + followHalf_content
        self.writeFile(self.fileName, content, 0)

    def deleteText2Input(self,event):
        if self.debug:
            print "Action Track: deleteTextInput"
        get_insert = self.answerText2.index(INSERT)
        print "delete insert:", get_insert
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1])-1)
        get_input = self.answerText2.get(last_insert, get_insert).encode('utf-8')
        # print "get_input: ", get_input
        aboveHalf_content = self.answerText2.get('1.0', last_insert).encode('utf-8')
        followHalf_content = self.answerText2.get(last_insert, "end-1c").encode('utf-8')
        if len(get_input) > 0:
            followHalf_content = followHalf_content.replace(get_input, '', 1)
        content = aboveHalf_content + followHalf_content
        self.writeFile(self.fileName, content, 1)

    def deleteText3Input(self,event):
        if self.debug:
            print "Action Track: deleteTextInput"
        get_insert = self.answerText3.index(INSERT)
        print "delete insert:", get_insert
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1])-1)
        get_input = self.answerText3.get(last_insert, get_insert).encode('utf-8')
        # print "get_input: ", get_input
        aboveHalf_content = self.answerText3.get('1.0', last_insert).encode('utf-8')
        followHalf_content = self.answerText3.get(last_insert, "end-1c").encode('utf-8')
        if len(get_input) > 0:
            followHalf_content = followHalf_content.replace(get_input, '', 1)
        content = aboveHalf_content + followHalf_content
        self.writeFile(self.fileName, content, 2)

    def deleteText4Input(self,event):
        if self.debug:
            print "Action Track: deleteTextInput"
        get_insert = self.answerText4.index(INSERT)
        print "delete insert:", get_insert
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1])-1)
        get_input = self.answerText4.get(last_insert, get_insert).encode('utf-8')
        # print "get_input: ", get_input
        aboveHalf_content = self.answerText4.get('1.0', last_insert).encode('utf-8')
        followHalf_content = self.answerText4.get(last_insert, "end-1c").encode('utf-8')
        if len(get_input) > 0:
            followHalf_content = followHalf_content.replace(get_input, '', 1)
        content = aboveHalf_content + followHalf_content
        self.writeFile(self.fileName, content, 3)

    def deleteText5Input(self, event):
        if self.debug:
            print "Action Track: deleteTextInput"
        get_insert = self.answerText5.index(INSERT)
        print "delete insert:", get_insert
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1]) - 1)
        get_input = self.answerText5.get(last_insert, get_insert).encode('utf-8')
        # print "get_input: ", get_input
        aboveHalf_content = self.answerText5.get('1.0', last_insert).encode('utf-8')
        followHalf_content = self.answerText5.get(last_insert, "end-1c").encode('utf-8')
        if len(get_input) > 0:
            followHalf_content = followHalf_content.replace(get_input, '', 1)
        content = aboveHalf_content + followHalf_content
        self.writeFile(self.fileName, content, 4)

    def replaceString(self, content, string, cursor_index):
        new_string = "[@" + string + "@]"
        newcursor_index = cursor_index.split('.')[0]+"."+str(int(cursor_index.split('.')[1])+4)

        content = content.replace(string, new_string, 1)
        return content, newcursor_index

    def writeFile(self, fileName, content, index):
        if len(fileName) > 0:
            self.form_json[self.currentQuestionID]["Responses"][self.currentBeginningAnswerID + index]=content
            newContent=json.dumps(self.form_json)

            if ".ann" in fileName:
                new_name = fileName
                ann_file = open(new_name, 'w')
                ann_file.write(newContent)
                ann_file.close()
            else:
                new_name = fileName+'.ann'
                ann_file = open(new_name, 'w')
                ann_file.write(newContent)
                ann_file.close()
            self.autoLoadNewFile(new_name)
            # self.generateSequenceFile()
        else:
            print "Don't write to empty file!"        

    def addRecommendContent(self, train_data, decode_data, recommendMode):
        if not recommendMode:
            content = train_data + decode_data
        else:
            if self.debug:
                print "Action Track: addRecommendContent, start Recommend entity"
            content = maximum_matching(train_data, decode_data)
        return content

    def setColorDisplay(self):
        if self.debug:
            print "Action Track: setColorDisplay"
        self.text.config(insertbackground='red', insertwidth=4, font=self.fnt)

        countVar = StringVar()
        currentCursor = self.text.index(INSERT)
        lineStart = currentCursor.split('.')[0] + '.0'
        lineEnd = currentCursor.split('.')[0] + '.end'
         
        if self.colorAllChunk:
            self.text.mark_set("matchStart", "1.0")
            self.text.mark_set("matchEnd", "1.0")
            self.text.mark_set("searchLimit", 'end-1c')
            self.text.mark_set("recommend_matchStart", "1.0")
            self.text.mark_set("recommend_matchEnd", "1.0")
            self.text.mark_set("recommend_searchLimit", 'end-1c')
        else:
            self.text.mark_set("matchStart", lineStart)
            self.text.mark_set("matchEnd", lineStart)
            self.text.mark_set("searchLimit", lineEnd)
            self.text.mark_set("recommend_matchStart", lineStart)
            self.text.mark_set("recommend_matchEnd", lineStart)
            self.text.mark_set("recommend_searchLimit", lineEnd)
        while True:
            self.text.tag_configure("catagory", background=self.entityColor)
            self.text.tag_configure("edge", background=self.entityColor)
            pos = self.text.search(self.entityRe, "matchEnd" , "searchLimit",  count=countVar, regexp=True)
            if pos =="":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            
            first_pos = pos
            second_pos = "%s+%sc" % (pos, str(1))
            lastsecond_pos = "%s+%sc" % (pos, str(int(countVar.get())-1))
            last_pos = "%s + %sc" %(pos, countVar.get())

            self.text.tag_add("catagory", second_pos, lastsecond_pos)
            self.text.tag_add("edge", first_pos, second_pos)
            self.text.tag_add("edge", lastsecond_pos, last_pos)   
        ## color recommend type
        while True:
            self.text.tag_configure("recommend", background=self.recommendColor)
            recommend_pos = self.text.search(self.recommendRe, "recommend_matchEnd" , "recommend_searchLimit",  count=countVar, regexp=True)
            if recommend_pos =="":
                break
            self.text.mark_set("recommend_matchStart", recommend_pos)
            self.text.mark_set("recommend_matchEnd", "%s+%sc" % (recommend_pos, countVar.get()))
            
            first_pos = recommend_pos
            # second_pos = "%s+%sc" % (recommend_pos, str(1))
            lastsecond_pos = "%s+%sc" % (recommend_pos, str(int(countVar.get())))
            self.text.tag_add("recommend", first_pos, lastsecond_pos)
            
        
        ## color the most inside span for nested span, scan from begin to end again  
        if self.colorAllChunk:
            self.text.mark_set("matchStart", "1.0")
            self.text.mark_set("matchEnd", "1.0")
            self.text.mark_set("searchLimit", 'end-1c')
        else:
            self.text.mark_set("matchStart", lineStart)
            self.text.mark_set("matchEnd", lineStart)
            self.text.mark_set("searchLimit", lineEnd)
        while True:
            self.text.tag_configure("insideEntityColor", background=self.insideNestEntityColor)
            pos = self.text.search(self.insideNestEntityRe , "matchEnd" , "searchLimit",  count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            first_pos = "%s + %sc" %(pos, 2)
            last_pos = "%s + %sc" %(pos, str(int(countVar.get())-1))
            self.text.tag_add("insideEntityColor", first_pos, last_pos)   
    
    def pushToHistory(self):
        if self.debug:
            print "Action Track: pushToHistory"
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print "push to history cursor: ", cursorPosition
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    def pushToHistoryEvent(self,event):
        if self.debug:
            print "Action Track: pushToHistoryEvent"
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print "push to history cursor: ", cursorPosition
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    ## update shortcut map
    def renewPressCommand(self):
        if self.debug:
            print "Action Track: renewPressCommand"
        seq = 0
        new_dict = {}
        listLength = len(self.labelEntryList)
        delete_num = 0
        for key in sorted(self.pressCommand):
            label = self.labelEntryList[seq].get()
            if len(label) > 0:
                new_dict[key] = label
            else: 
                delete_num += 1
            seq += 1
        self.pressCommand = new_dict
        for idx in range(1, delete_num+1):
            self.labelEntryList[listLength-idx].delete(0,END)
            self.shortcutLabelList[listLength-idx].config(text="NON= ") 
        with open(self.configFile, 'wb') as fp:
            pickle.dump(self.pressCommand, fp)
        self.setMapShow()
        tkMessageBox.showinfo("Remap Notification", "Shortcut map has been updated!\n\nConfigure file has been saved in File:" + self.configFile)

    def autoLoadNewFile(self, fileName):
        if len(fileName) > 0:
            text = self.readFile(fileName)
            self.form_json = json.loads(text)

            if self.form_json:
                self.currentTextQuestionBrief = self.form_json[self.currentQuestionID]
                questionText = self.currentTextQuestionBrief["Title"]
                self.question.delete("1.0", END)
                self.question.insert(END, questionText)
                responseList = self.currentTextQuestionBrief["Responses"]
                for i in range(0, 5):
                    currentAnswerID = self.currentBeginningAnswerID + i
                    if currentAnswerID < len(responseList):
                        if i == 0:
                            self.answerText1.delete("1.0", END)
                            self.answerText1.insert(END, responseList[currentAnswerID])
                        if i == 1:
                            self.answerText2.delete("1.0", END)
                            self.answerText2.insert(END, responseList[currentAnswerID])
                        if i == 2:
                            self.answerText3.delete("1.0", END)
                            self.answerText3.insert(END, responseList[currentAnswerID])
                        if i == 3:
                            self.answerText4.delete("1.0", END)
                            self.answerText4.insert(END, responseList[currentAnswerID])
                        if i == 4:
                            self.answerText5.delete("1.0", END)
                            self.answerText5.insert(END, responseList[currentAnswerID])
                    else:
                        break

    ## show shortcut map
    def setMapShow(self):
        if os.path.isfile(self.configFile):
            with open (self.configFile, 'rb') as fp:
                self.pressCommand = pickle.load(fp)
        hight = len(self.pressCommand)
        width = 2
        row = 0
        mapLabel = Label(self, text ="Shortcuts map Labels", foreground="blue", font=(self.textFontStyle, 14, "bold"))
        mapLabel.grid(row=0, column = self.textColumn + 2, columnspan=2, rowspan = 1, padx = 10)
        self.labelEntryList = []
        self.shortcutLabelList = []
        for key in sorted(self.pressCommand):
            row += 1
            # print "key: ", key, "  command: ", self.pressCommand[key]
            symbolLabel = Label(self, text =key.upper() + ": ", foreground="blue", font=(self.textFontStyle, 14, "bold"))
            symbolLabel.grid(row=row, column = self.textColumn +2,columnspan=1, rowspan = 1, padx = 3)
            self.shortcutLabelList.append(symbolLabel)

            labelEntry = Entry(self, foreground="blue", font=(self.textFontStyle, 14, "bold"))
            labelEntry.insert(0, self.pressCommand[key])
            labelEntry.grid(row=row, column = self.textColumn +3, columnspan=1, rowspan = 1)
            self.labelEntryList.append(labelEntry)
            # print "row: ", row


    def getCursorIndex(self):
        return self.text.index(INSERT)


    def generateSequenceFile(self):
        if (".ann" not in self.fileName) and (".txt" not in self.fileName): 
            out_error = "Export only works on filename ended in .ann or .txt!\nPlease rename file."
            print out_error
            tkMessageBox.showerror("Export error!", out_error)

            return -1
        fileLines = open(self.fileName, 'rU').readlines()
        lineNum = len(fileLines)
        new_filename = self.fileName.split('.ann')[0]+ '.anns'
        seqFile = open(new_filename, 'w')
        for line in fileLines:
            if len(line) <= 2:
                seqFile.write('\n')
                continue
            else:
                if not self.keepRecommend:
                    line = removeRecommendContent(line, self.recommendRe)
                wordTagPairs = getWordTagPairs(line, self.seged, self.tagScheme, self.onlyNP, self.goldAndrecomRe)
                for wordTag in wordTagPairs:
                    seqFile.write(wordTag)
                ## use null line to seperate sentences
                seqFile.write('\n')
        seqFile.close()
        print "Exported file into sequence style in file: ",new_filename
        print "Line number:",lineNum
        showMessage =  "Exported file successfully!\n\n"   
        showMessage += "Tag scheme: " +self.tagScheme + "\n\n"
        showMessage += "Keep Recom: " +str(self.keepRecommend) + "\n\n"
        showMessage += "Text Seged: " +str(self.seged) + "\n\n"
        showMessage += "Line Number: " + str(lineNum)+ "\n\n"
        showMessage += "Saved to File: " + new_filename
        tkMessageBox.showinfo("Export Message", showMessage)


def getWordTagPairs(tagedSentence, seged=True, tagScheme="BMES", onlyNP=False, entityRe=r'\[\@.*?\#.*?\*\]'):
    newSent = tagedSentence.strip('\n').decode('utf-8')
    filterList = re.findall(entityRe, newSent)
    newSentLength = len(newSent)
    chunk_list = []
    start_pos = 0
    end_pos = 0
    if len(filterList) == 0:
        singleChunkList = []
        singleChunkList.append(newSent)
        singleChunkList.append(0)
        singleChunkList.append(len(newSent))
        singleChunkList.append(False)
        chunk_list.append(singleChunkList)
        # print singleChunkList
        singleChunkList = []
    else:
        for pattern in filterList:
            # print pattern
            singleChunkList = []
            start_pos = end_pos + newSent[end_pos:].find(pattern)
            end_pos = start_pos + len(pattern)
            singleChunkList.append(pattern)
            singleChunkList.append(start_pos)
            singleChunkList.append(end_pos)
            singleChunkList.append(True)
            chunk_list.append(singleChunkList)
            singleChunkList = []
    ## chunk_list format:
    full_list = []
    for idx in range(0, len(chunk_list)):
        if idx == 0:
            if chunk_list[idx][1] > 0:
                full_list.append([newSent[0:chunk_list[idx][1]], 0, chunk_list[idx][1], False])
                full_list.append(chunk_list[idx])
            else:
                full_list.append(chunk_list[idx])
        else:
            if chunk_list[idx][1] == chunk_list[idx-1][2]:
                full_list.append(chunk_list[idx])
            elif chunk_list[idx][1] < chunk_list[idx-1][2]:
                print "ERROR: found pattern has overlap!", chunk_list[idx][1], ' with ', chunk_list[idx-1][2]
            else:
                full_list.append([newSent[chunk_list[idx-1][2]:chunk_list[idx][1]], chunk_list[idx-1][2], chunk_list[idx][1], False])
                full_list.append(chunk_list[idx])

        if idx == len(chunk_list) - 1 :
            if chunk_list[idx][2] > newSentLength:
                print "ERROR: found pattern position larger than sentence length!"
            elif chunk_list[idx][2] < newSentLength:
                full_list.append([newSent[chunk_list[idx][2]:newSentLength], chunk_list[idx][2], newSentLength, False])
            else:
                continue
    return turnFullListToOutputPair(full_list, seged, tagScheme, onlyNP)


def turnFullListToOutputPair(fullList, seged=True, tagScheme="BMES", onlyNP=False):
    pairList = []
    for eachList in fullList:
        if eachList[3]:
            contLabelList = eachList[0].strip('[@$]').rsplit('#', 1)
            if len(contLabelList) != 2:
                print "Error: sentence format error!"
            label = contLabelList[1].strip('*')
            if seged:
                contLabelList[0] = contLabelList[0].split()
            if onlyNP:
                label = "NP"
            outList = outputWithTagScheme(contLabelList[0], label, tagScheme)
            for eachItem in outList:
                pairList.append(eachItem)
        else:
            if seged:
                eachList[0] = eachList[0].split()
            for idx in range(0, len(eachList[0])):
                basicContent = eachList[0][idx]
                if basicContent == ' ': 
                    continue
                pair = basicContent + ' ' + 'O\n'
                pairList.append(pair.encode('utf-8'))
    return pairList


def outputWithTagScheme(input_list, label, tagScheme="BMES"):
    output_list = []
    list_length = len(input_list)
    if tagScheme=="BMES":
        if list_length ==1:
            pair = input_list[0]+ ' ' + 'S-' + label + '\n'
            output_list.append(pair.encode('utf-8'))
        else:
            for idx in range(list_length):
                if idx == 0:
                    pair = input_list[idx]+ ' ' + 'B-' + label + '\n'
                elif idx == list_length -1:
                    pair = input_list[idx]+ ' ' + 'E-' + label + '\n'
                else:
                    pair = input_list[idx]+ ' ' + 'M-' + label + '\n'
                output_list.append(pair.encode('utf-8'))
    else:
        for idx in range(list_length):
            if idx == 0:
                pair = input_list[idx]+ ' ' + 'B-' + label + '\n'
            else:
                pair = input_list[idx]+ ' ' + 'I-' + label + '\n'
            output_list.append(pair.encode('utf-8'))
    return output_list


def removeRecommendContent(content, recommendRe = r'\[\$.*?\#.*?\*\](?!\#)'):
    output_content = ""
    last_match_end = 0
    for match in re.finditer(recommendRe, content):
        matched =content[match.span()[0]:match.span()[1]]
        words = matched.strip('[$]').split("#")[0]
        output_content += content[last_match_end:match.span()[0]] + words
        last_match_end = match.span()[1]
    output_content += content[last_match_end:]
    return output_content

def decompositCommand(command_string):
    command_list = []
    each_command = []
    num_select = ''
    for idx in range(0, len(command_string)):
        if command_string[idx].isdigit():
            num_select += command_string[idx]
        else:
            each_command.append(num_select)
            each_command.append(command_string[idx])
            command_list.append(each_command)
            each_command = []
            num_select =''
    # print command_list
    return command_list

def main():
    print("SUTDAnnotator launched!")
    print(("OS:%s")%(platform.system()))
    root = Tk()
    root.geometry("1300x800+200+200")
    app = Example(root)
    app.setFont(17)
    root.mainloop()  

if __name__ == '__main__':
    main()





