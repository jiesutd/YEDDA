# -*- coding: utf-8 -*-
# @Author: Jie Yang from SUTD
# @Date:   2016-Jan-06 17:11:59
# @Last Modified by:   Jie     @Contact: jieynlp@gmail.com
# @Last Modified time: 2017-05-03 14:57:56
#!/usr/bin/env python
# coding=utf-8

from Tkinter import *
from ttk import *#Frame, Button, Label, Style, Scrollbar
import tkFileDialog
import tkFont
import re
from collections import deque
import pickle
import os.path


class Example(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.fileName = ""
        self.history = deque(maxlen=20)
        self.currentContent = deque(maxlen=1)
        self.pressCommand = {'a':"Location",
                             'b':"Org-Government",
                             'c':"Org-Company",
                             'd':"Org-Media",
                             'e':"Org-Other",
                             'f':"Person-Name",
                             'g':"Person-Title",
                             'h':"Person-Title",
                             'i':"Person-Combine", 
                             'j':"Arti-Policy",
                             'k':"Arti-Project",
                             'l':"Arti-Product", 
                             'm':"Arti-Service", 
                             'n':"Arti-Technology",
                             'o':"Arti-Document",
                             'p':"Arti-Other", 
                             'r':"Event", 
                             's': "Sector",
                             't': "Fin-Concept",
                             'u':"Other"}
        self.allKey = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.controlCommand = {'q':"unTag", 'ctrl+z':'undo'}
        self.labelEntryList = []
        self.shortcutLabelList = []
        # default GUI display parameter
        self.textRow = 25
        self.textColumn = 5
        self.tagScheme = "BMES"
        self.onlyNP = False  ## for exporting sequence 
        self.seged = True
        self.configFile = "config"
        self.colorAllChunk = True
        self.entityRe = r'\[\@.*?\#.*?\*\]'
        ## configure color
        self.entityColor = "LightSkyBlue1"
        self.selectColor = 'light salmon'
        self.initUI()
        
        
    def initUI(self):
      
        self.parent.title("SUTDNLP Annotation Tool-V0.5.3")
        self.pack(fill=BOTH, expand=True)
        
        for idx in range(0,self.textColumn):
            self.columnconfigure(idx, weight =2)
        # self.columnconfigure(0, weight=2)
        self.columnconfigure(self.textColumn+2, weight=1)
        self.columnconfigure(self.textColumn+4, weight=1)
        for idx in range(0,16):
            self.rowconfigure(idx, weight =1)
        # self.rowconfigure(5, weight=1)
        # self.rowconfigure(5, pad=7)
        
        self.lbl = Label(self, text="File: no file is opened")
        self.lbl.grid(sticky=W, pady=4, padx=5)
        self.fnt = tkFont.Font(family="Helvetica",size=self.textRow,weight="bold",underline=0)
        self.text = Text(self, font=self.fnt, selectbackground=self.selectColor)
        self.text.grid(row=1, column=0, columnspan=self.textColumn, rowspan=self.textRow, padx=12, sticky=E+W+S+N)

        self.sb = Scrollbar(self)
        self.sb.grid(row = 1, column = self.textColumn, rowspan = self.textRow, padx=0, sticky = E+W+S+N)
        self.text['yscrollcommand'] = self.sb.set 
        self.sb['command'] = self.text.yview 
        # self.sb.pack()

        abtn = Button(self, text="Open", command=self.onOpen)
        abtn.grid(row=1, column=self.textColumn +1)

        ubtn = Button(self, text="Remap", command=self.renewPressCommand)
        ubtn.grid(row=2, column=self.textColumn +1, pady=4)

        exportbtn = Button(self, text="Export", command=self.generateSequenceFile)
        exportbtn.grid(row=3, column=self.textColumn + 1, pady=4)

        cbtn = Button(self, text="Quit", command=self.quit)
        cbtn.grid(row=4, column=self.textColumn + 1, pady=4)

        self.cursorName = Label(self, text="Cursor: ", foreground="red", font=("Helvetica", 14, "bold"))
        self.cursorName.grid(row=5, column=self.textColumn +1, pady=4)
        self.cursorIndex = Label(self, text="", foreground="red", font=("Helvetica", 14, "bold"))
        self.cursorIndex.grid(row=6, column=self.textColumn + 1, pady=4)

        lbl_entry = Label(self, text="Command:")
        lbl_entry.grid(row = self.textRow +1,  sticky = E+W+S+N, pady=4,padx=4)
        self.entry = Entry(self)
        self.entry.grid(row = self.textRow +1, columnspan=self.textColumn + 1, rowspan = 1, sticky = E+W+S+N, pady=4, padx=80)
        self.entry.bind('<Return>', self.returnEnter)

        
        # for press_key in self.pressCommand.keys():
        for idx in range(0, len(self.allKey)):
            press_key = self.allKey[idx]
            self.text.bind(press_key, lambda event, arg=press_key:self.textReturnEnter(event,arg))
            simplePressKey = "<KeyRelease-" + press_key + ">"
            self.text.bind(simplePressKey, self.deleteTextInput)
            controlPlusKey = "<Control-Key-" + press_key + ">"
            self.text.bind(controlPlusKey, self.keepCurrent)
            altPlusKey = "<Command-Key-" + press_key + ">"
            self.text.bind(altPlusKey, self.keepCurrent)

        self.text.bind('<Control-Key-z>', self.backToHistory)
        ## disable the default  copy behaivour when right click. For MacOS, right click is button 2, other systems are button3
        self.text.bind('<Button-2>', self.rightClick)
        self.text.bind('<Button-3>', self.rightClick)

        self.text.bind('<Double-Button-1>', self.doubleLeftClick)
        self.text.bind('<ButtonRelease-1>', self.singleLeftClick)

        self.setMapShow()

        self.enter = Button(self, text="Enter", command=self.returnButton)
        self.enter.grid(row=self.textRow +1, column=self.textColumn +1) 
    
    ## cursor index show with the left click
    def singleLeftClick(self, event):
        cursor_index = self.text.index(INSERT) 
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s\ncol: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)

    
    ## TODO: select entity by double left click
    def doubleLeftClick(self, event):
        pass
        # cursor_index = self.text.index(INSERT)
        # start_index = ("%s - %sc" % (cursor_index, 5))
        # end_index = ("%s + %sc" % (cursor_index, 5))
        # self.text.tag_add('SEL', '1.0',"end-1c")
        
        

    ## Disable right click default copy selection behaviour
    def rightClick(self, event):
        try:
            firstSelection_index = self.text.index(SEL_FIRST)
            cursor_index = self.text.index(SEL_LAST)
            content = self.text.get('1.0',"end-1c").encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            pass



    def onOpen(self):
        ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')]
        dlg = tkFileDialog.Open(self, filetypes = ftypes)
        # file_opt = options =  {}
        # options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
        # dlg = tkFileDialog.askopenfilename(**options)
        fl = dlg.show()
        if fl != '':
            self.text.delete("1.0",END)
            text = self.readFile(fl)
            self.text.insert(END, text)
            self.setNameLabel("File: " + fl)
            self.setDisplay()
            # self.initAnnotate()
            self.text.mark_set(INSERT, "1.0")
            self.setCursorLabel(self.text.index(INSERT))

    def readFile(self, filename):
        f = open(filename, "rU")
        text = f.read()
        self.fileName = filename
        return text

    def setFont(self, value):
        _family="Helvetica"
        _size = value
        _weight="bold"
        _underline=0
        fnt = tkFont.Font(family= _family,size= _size,weight= _weight,underline= _underline)
        Text(self, font=fnt)
    
    def setNameLabel(self, new_file):
        self.lbl.config(text=new_file)

    def setCursorLabel(self, cursor_index):
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s\ncol: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)

    # def initAnnotate():
    #     text = self.text.get('1.0','end-1c')
        

    def returnButton(self):
        self.pushToHistory()
        # self.returnEnter(event)
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content


    def returnEnter(self,event):
        self.pushToHistory()
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content


    def textReturnEnter(self,event, press_key):
        self.pushToHistory()
        # print "event: ", press_key
        # content = self.text.get()
        self.clearCommand()
        self.executeCursorCommand(press_key.lower())
        # self.deleteTextInput()
        return press_key


    def backToHistory(self,event):
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
        self.text.insert(INSERT, 'p')


    def clearCommand(self):
        self.entry.delete(0, 'end')


    def getText(self):
        textContent = self.text.get("1.0","end-1c")
        textContent = textContent.encode('utf-8')
        return textContent

    def executeCursorCommand(self,command):
        content = self.getText()
        try:
            firstSelection_index = self.text.index(SEL_FIRST)
            cursor_index = self.text.index(SEL_LAST)
            aboveHalf_content = self.text.get('1.0',firstSelection_index)
            followHalf_content = self.text.get(firstSelection_index, "end-1c")
            selected_string = self.text.selection_get()
            if re.match(self.entityRe,selected_string) != None : 
                ## if have selected entity
                new_string_list = selected_string.strip('[@]').rsplit('#',1)
                new_string = new_string_list[0]
                followHalf_content = followHalf_content.replace(selected_string, new_string, 1)
                selected_string = new_string
                cursor_index = "%s - %sc" % (cursor_index, str(len(new_string_list[1])+4))
            if command == "q":
                print 'q: remove entity label'
            else:
                if len(selected_string) > 0:
                    followHalf_content, cursor_index = self.replaceString(followHalf_content, selected_string, command, cursor_index)
            content = aboveHalf_content + followHalf_content
            content = content.encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            ## not select text
            cursor_index = self.text.index(INSERT)
            [line_id, column_id] = cursor_index.split('.')
            aboveLine_content =  self.text.get('1.0', str(int(line_id)-1) + '.end')
            belowLine_content = self.text.get(str(int(line_id)+1)+'.0', "end-1c")
            line = self.text.get(line_id + '.0', line_id + '.end')
            matched_span =  (-1,-1)
            for match in re.finditer(self.entityRe, line):
                if  match.span()[0]<= int(column_id) & int(column_id) <= match.span()[1]:
                    matched_span = match.span()
                    break
            if matched_span[1] > 0 :
                selected_string = line[matched_span[0]:matched_span[1]]
                new_string_list = selected_string.strip('[@]').rsplit('#',1)
                new_string = new_string_list[0]
                line = line[:matched_span[0]] + new_string + line[matched_span[1]:]
                # line = line.replace(selected_string, new_string, 1)
                selected_string = new_string
                cursor_index = line_id + '.'+ str(int(matched_span[1])-(len(new_string_list[1])+4))
                if command == "q":
                    print 'q: remove entity label'
                else:
                    if len(selected_string) > 0:
                        if command in self.pressCommand:
                            line, cursor_index = self.replaceString(line, selected_string, command, cursor_index)
                        else:
                            return
            if aboveLine_content != '':
                aboveLine_content = aboveLine_content+ '\n'
            if belowLine_content != '':
                belowLine_content = '\n' + belowLine_content
            content = aboveLine_content + line+ belowLine_content
            content = content.encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)


    def executeEntryCommand(self,command):
        if len(command) == 0:
            currentCursor = self.text.index(INSERT)
            newCurrentCursor = str(int(currentCursor.split('.')[0])+1) + ".0"
            self.text.mark_set(INSERT, newCurrentCursor)
            self.setCursorLabel(newCurrentCursor)
        else:
            command_list = decompositCommand(command)
            for idx in range(0, len(command_list)):
                command = command_list[idx]
                if len(command) == 2:
                    select_num = int(command[0])
                    command = command[1]
                    content = self.getText()
                    cursor_index = self.text.index(INSERT)
                    newcursor_index = cursor_index.split('.')[0]+"."+str(int(cursor_index.split('.')[1])+select_num)
                    # print "new cursor position: ", select_num, " with ", newcursor_index, "with ", newcursor_index
                    selected_string = self.text.get(cursor_index, newcursor_index).encode('utf-8')
                    aboveHalf_content = self.text.get('1.0',cursor_index).encode('utf-8')
                    followHalf_content = self.text.get(cursor_index, "end-1c").encode('utf-8')
                    if command in self.pressCommand:
                        if len(selected_string) > 0:
                            # print "insert index: ", self.text.index(INSERT) 
                            followHalf_content, newcursor_index = self.replaceString(followHalf_content, selected_string, command, newcursor_index)
                            content = aboveHalf_content + followHalf_content
                    self.writeFile(self.fileName, content, newcursor_index)
            

    def deleteTextInput(self,event):
        get_insert = self.text.index(INSERT)
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1])-1)
        get_input = self.text.get(last_insert, get_insert).encode('utf-8')
        # print "get_input: ", get_input
        aboveHalf_content = self.text.get('1.0',last_insert).encode('utf-8')
        followHalf_content = self.text.get(last_insert, "end-1c").encode('utf-8')
        if len(get_input) > 0: 
            followHalf_content = followHalf_content.replace(get_input, '', 1)
            content = aboveHalf_content + followHalf_content
        self.writeFile(self.fileName, content, last_insert)



    def replaceString(self, content, string, replaceType, cursor_index):
        if replaceType in self.pressCommand:
            new_string = "[@" + string + "#" + self.pressCommand[replaceType] + "*]" 
            cursor_indexList = cursor_index.split('.') 
            newcursor_index = "%s + %sc" % (cursor_index, str(len(self.pressCommand[replaceType])+5))
            # newcursor_index = cursor_indexList[0] + "." + str(int(cursor_indexList[1])+ len(new_string))
        else:
            print "Invaild command!"  
            print "cursor index: ", self.text.index(INSERT)  
            return content, cursor_index
        # print "new string: ", new_string
        # print "find: ", content.find(string)
        content = content.replace(string, new_string, 1)
        # print "content: ", content
        return content, newcursor_index


    def writeFile(self, fileName, content, newcursor_index):
        if len(fileName) > 0:
            if ".ann" in fileName:
                new_name = fileName
                ann_file = open(new_name, 'w')
                ann_file.write(content)
                ann_file.close()
            else:
                new_name = fileName+'.ann'
                ann_file = open(new_name, 'w')
                ann_file.write(content)
                ann_file.close()   
            # print "Writed to new file: ", new_name 
            self.autoLoadNewFile(new_name, newcursor_index)
            # self.generateSequenceFile()
        else:
            print "Don't write to empty file!"        


    def autoLoadNewFile(self, fileName, newcursor_index):
        if len(fileName) > 0:
            self.text.delete("1.0",END)
            text = self.readFile(fileName)
            self.text.insert("end-1c", text)
            self.setNameLabel("File: " + fileName)
            self.text.mark_set(INSERT, newcursor_index)
            self.text.see(newcursor_index)
            self.setCursorLabel(newcursor_index)
            self.setLineDisplay()
            

    def setLineDisplay(self):
        self.text.config(insertbackground='red', insertwidth=4, font=self.fnt)

        countVar = StringVar()
        currentCursor = self.text.index(INSERT)
        lineStart = currentCursor.split('.')[0] + '.0'
        lineEnd = currentCursor.split('.')[0] + '.end'
         
        if self.colorAllChunk:
            self.text.mark_set("matchStart", "1.0")
            self.text.mark_set("matchEnd", "1.0")
            self.text.mark_set("searchLimit", 'end-1c')
        else:
            self.text.mark_set("matchStart", lineStart)
            self.text.mark_set("matchEnd", lineStart)
            self.text.mark_set("searchLimit", lineEnd)
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



    def setDisplay(self):
        self.text.config(insertbackground='red', insertwidth=4)
        self.text.mark_set("matchStart", "1.0")
        self.text.mark_set("matchEnd", "1.0") 
        self.text.mark_set("searchLimit", 'end-1c')

        countVar = StringVar()
        # for annotate_type in self.pressCommand.values():
        while True:
            # self.text.tag_configure("catagory", background="LightSkyBlue1")
            # self.text.tag_configure("edge", background="LightSkyBlue1")
            self.text.tag_configure("catagory", background=self.entityColor)
            self.text.tag_configure("edge", background=self.entityColor)
            pos = self.text.search(self.entityRe, "matchEnd" , "searchLimit",  count=countVar, regexp=True)
            if pos == "":
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
            
    
    def pushToHistory(self):
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print "push to history cursor: ", cursorPosition
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    def pushToHistoryEvent(self,event):
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print "push to history cursor: ", cursorPosition
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    ## update shortcut map
    def renewPressCommand(self):
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

    ## show shortcut map
    def setMapShow(self):
        if os.path.isfile(self.configFile):
            with open (self.configFile, 'rb') as fp:
                self.pressCommand = pickle.load(fp)
        hight = len(self.pressCommand)
        width = 2
        row = 0
        mapLabel = Label(self, text ="Shortcuts map Labels", foreground="blue", font=("Helvetica", 14, "bold"))
        mapLabel.grid(row=0, column = self.textColumn +2,columnspan=2, rowspan = 1, padx = 10)
        self.labelEntryList = []
        self.shortcutLabelList = []
        for key in sorted(self.pressCommand):
            row += 1
            # print "key: ", key, "  command: ", self.pressCommand[key]
            symbolLabel = Label(self, text =key + ": ", foreground="blue", font=("Helvetica", 14, "bold"))
            symbolLabel.grid(row=row, column = self.textColumn +2,columnspan=1, rowspan = 1, padx = 3)
            self.shortcutLabelList.append(symbolLabel)

            labelEntry = Entry(self, foreground="blue", font=("Helvetica", 14, "bold"))
            labelEntry.insert(0, self.pressCommand[key])
            labelEntry.grid(row=row, column = self.textColumn +3, columnspan=1, rowspan = 1)
            self.labelEntryList.append(labelEntry)
            # print "row: ", row


    def getCursorIndex(self):
        return self.text.index(INSERT)


    def generateSequenceFile(self):
        if (".ann" not in self.fileName) and (".txt" not in self.fileName): 
            print "Export only works on filename ended in .ann or .txt! Please rename file."
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
                wordTagPairs = getWordTagPairs(line, self.seged, self.tagScheme, self.onlyNP, self.entityRe)
                for wordTag in wordTagPairs:
                    seqFile.write(wordTag)
                ## use null line to seperate sentences
                seqFile.write('\n')
        seqFile.close()
        print "Exported file into sequence style in file: ",new_filename
        print "Line number:",lineNum


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
            contLabelList = eachList[0].strip('[@]').rsplit('#', 1)
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
    root = Tk()
    root.geometry("1300x700+200+200")
    app = Example(root)
    app.setFont(17)
    root.mainloop()  


if __name__ == '__main__':
    main()





