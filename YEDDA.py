# -*- coding: utf-8 -*-
import os.path
import platform
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox
from collections import deque
from tkinter import *
from tkinter.ttk import Frame, Button, Radiobutton, Label, Combobox, Scrollbar
from tkinter.simpledialog import Dialog
from tkinter.scrolledtext import ScrolledText
from dataclasses import dataclass
from typing import List

from utils.recommend import *


class Editor(ScrolledText):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        fnt = font.Font(family='Times', size=20, weight="bold", underline=0)
        self.config(insertbackground='red', insertwidth=4, font=fnt)
        edge_fnt = font.Font(family='Times', size=12, underline=0)
        self.tag_configure("edge", background="light grey", foreground='DimGrey', font=edge_fnt)
        self.tag_configure("recommend", background='light green')
        self.tag_configure("category", background="SkyBlue1")

        def _ignore(e): return 'break'

        # Disable the default  copy behaivour when right click.
        # For MacOS, right click is button 2, other systems are button3
        self.bind('<Button-2>', _ignore)
        self.bind('<Button-3>', _ignore)

    def _highlight_entity(self, start: str, count: int, tagname: str):
        end = f'{start}+{count}c'
        star_pos = self.get(start, end).rfind('#')
        word_start = f"{start}+2c"
        word_end = f"{start}+{star_pos}c"
        self.tag_add(tagname, word_start, word_end)
        self.tag_add("edge", start, word_start)
        self.tag_add("edge", word_end, end)

    def show_annotation_tag(self, show: bool):
        self.tag_configure('edge', elide=not show)

    def highlight_recommend(self, start: str, count: int):
        self._highlight_entity(start, count, 'recommend')

    def highlight_entity(self, start: str, count: int):
        self._highlight_entity(start, count, 'category')

    def get_text(self) -> str:
        """get text from 0 to end"""
        return self.get("1.0", "end-1c")


@dataclass
class KeyDef:
    key: str
    name: str
    desc: str = ''
    color: str = None


class KeyMapFrame(Frame):
    def __init__(self, parent, keymap: List[KeyDef]):
        super().__init__(parent, relief='groove')
        self.keymap = sorted(keymap, key=lambda x: x.key)
        self.rows = len(keymap)
        self.textFontStyle = 'Times'
        self.key_labels = []
        self.name_entries = []
        self.create_widgets()

    def create_widgets(self):
        title = Label(self, text="Shortcuts map", foreground="blue", font=(self.textFontStyle, 14, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky=W, padx=6, pady=8)
        for row, item in enumerate(self.keymap, 1):
            key_lbl = Label(self, text=item.key.upper() + ": ", font=(self.textFontStyle, 14, "bold"))
            key_lbl.grid(row=row, column=0, sticky=NW, padx=4, pady=4)
            self.key_labels.append(key_lbl)

            name_entry = Entry(self, font=(self.textFontStyle, 14))
            name_entry.insert(0, item.name)
            name_entry.grid(row=row, column=1, columnspan=1, rowspan=1, sticky=NW, padx=4, pady=4)
            self.name_entries.append(name_entry)

    def update_keymap(self, keymap):
        self.keymap = sorted(keymap, key=lambda x: x.key)
        for lbl in self.key_labels:
            lbl.destroy()
        for ent in self.name_entries:
            ent.destroy()
        self.key_labels = []
        self.name_entries = []
        self.create_widgets()

    def read_keymap(self) -> List[KeyDef]:
        """read current keymap in GUI, might be changed by user"""
        new_map = []
        for i, cmd in enumerate(self.keymap):
            new_name = self.name_entries[i].get()
            if new_name.strip() != '':
                new_map.append(KeyDef(cmd.key, new_name, cmd.desc, cmd.color))
            else:
                print(f'{cmd.key} key deleted')
        return new_map


class QueryExport(Dialog):
    def __init__(self, parent, filename, sample):
        self.confirmed = False
        self.sample = sample
        super().__init__(parent, 'Exporting to ' + filename)  # here dialog shows

    def body(self, master):
        """override"""
        box = Frame(master, relief='groove')
        self.scheme_var = StringVar(master, "BMES")
        Radiobutton(box, text="BMES", variable=self.scheme_var, value="BMES").pack(side=LEFT, padx=5, pady=5)
        Radiobutton(box, text="BIO", variable=self.scheme_var, value="BIO").pack(side=LEFT, padx=5, pady=5)
        box.pack()
        self.segmented_var = BooleanVar(master, self._guess_segmented())
        Checkbutton(master, text="Segmented", variable=self.segmented_var).pack()
        self.only_NP_var = BooleanVar(master, False)
        Checkbutton(master, text="Only NP label", variable=self.only_NP_var).pack()

    def apply(self):
        """override, called after press ok, not called on cancel"""
        self.confirmed = True

    def segmented(self) -> bool:
        return self.segmented_var.get()

    def only_NP(self) -> bool:
        return self.only_NP_var.get()

    def tag_scheme(self) -> str:
        return self.scheme_var.get()

    def _guess_segmented(self):
        """False for non-segmented Chinese, True for English or Segmented Chinese.
        Make naive guess, user should check whether the guess is right
        """
        ascii_percent = sum(1 for c in self.sample if c.isascii()) / len(self.sample)
        is_english = (ascii_percent > 0.8)
        space_percent = self.sample.count(' ') / len(self.sample)
        many_space = (space_percent > 0.2)
        return is_english or many_space or False


class Application(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.Version = "YEDDA-V1.0 Annotator"
        self.OS = platform.system().lower()
        self.fileName = ""
        self.debug = False
        self.colorAllChunk = True
        self.use_recommend = BooleanVar(self, True)
        self.history = deque(maxlen=20)
        self.currentContent = deque(maxlen=1)
        self.pressCommand = [KeyDef('a', "Artifical"),
                             KeyDef('b', "Event"),
                             KeyDef('c', "Fin-Concept"),
                             KeyDef('d', "Location"),
                             KeyDef('e', "Organization"),
                             KeyDef('f', "Person"),
                             KeyDef('g', "Sector"),
                             KeyDef('h', "Other")]
        self.labelEntryList = []
        self.shortcutLabelList = []
        self.configListLabel = None
        self.configListBox = None
        self.file_encoding = 'utf-8'

        # default GUI display parameter
        if len(self.pressCommand) > 20:
            self.textRow = len(self.pressCommand)
        else:
            self.textRow = 20
        self.textColumn = 5
        self.keepRecommend = True

        self.configFile = "configs/default.config"
        self.entity_regex = r'\[\@.*?\#.*?\*\](?!\#)'
        self.insideNestEntityRe = r'\[\@\[\@(?!\[\@).*?\#.*?\*\]\#'
        self.recommendRe = r'\[\$.*?\#.*?\*\](?!\#)'
        self.goldAndrecomRe = r'\[\@.*?\#.*?\*\](?!\#)'
        if self.keepRecommend:
            self.goldAndrecomRe = r'\[[\@\$)].*?\#.*?\*\](?!\#)'
        ## configure color
        self.insideNestEntityColor = "light slate blue"
        self.selectColor = 'light salmon'
        self.textFontStyle = "Times"
        self.initUI()

    def initUI(self):
        self.master.title(self.Version)
        self.pack(fill=BOTH, expand=True)

        for i in range(0, self.textColumn):
            self.columnconfigure(i, weight=2)
        # self.columnconfigure(0, weight=2)
        self.columnconfigure(self.textColumn + 2, weight=1)
        self.columnconfigure(self.textColumn + 4, weight=1)
        for i in range(0, 16):
            self.rowconfigure(i, weight=1)

        self.filename_lbl = Label(self, text="File: no file is opened")
        self.filename_lbl.grid(sticky=W, pady=4, padx=5)
        self.text = Editor(self, selectbackground=self.selectColor)
        self.text.grid(row=1, column=0, columnspan=self.textColumn, rowspan=self.textRow, padx=12, sticky=E + W + S + N)

        abtn = Button(self, text="Open", command=self.onOpen)
        abtn.grid(row=1, column=self.textColumn + 1)

        ubtn = Button(self, text="ReMap", command=self.renewPressCommand)
        ubtn.grid(row=2, column=self.textColumn + 1, pady=4)

        ubtn = Button(self, text="NewMap", command=self.savenewPressCommand)
        ubtn.grid(row=3, column=self.textColumn + 1, pady=4)

        exportbtn = Button(self, text="Export", command=self.generateSequenceFile)
        exportbtn.grid(row=4, column=self.textColumn + 1, pady=4)

        cbtn = Button(self, text="Quit", command=self.quit)
        cbtn.grid(row=5, column=self.textColumn + 1, pady=4)

        recommend_check = Checkbutton(self, text='Recommend', command=self.toggle_use_recommend,
                                      variable=self.use_recommend)
        recommend_check.grid(row=6, column=self.textColumn + 1, sticky=W, pady=4)

        show_tags_var = BooleanVar(self, True)
        show_tags_check = Checkbutton(self, text='Show Tags', variable=show_tags_var,
                                      command=lambda: self.text.show_annotation_tag(show_tags_var.get()))
        show_tags_check.grid(row=7, column=self.textColumn + 1, sticky=W)

        self.cursor_index_label = Label(self, text="1:0", foreground="red", font=(self.textFontStyle, 14, "bold"))
        self.cursor_index_label.grid(row=10, column=self.textColumn + 1, pady=4)

        lbl_entry = Label(self, text="Command:")
        lbl_entry.grid(row=self.textRow + 1, sticky=E + W + S + N, pady=4, padx=4)
        self.entry = Entry(self)
        self.entry.grid(row=self.textRow + 1, columnspan=self.textColumn + 1, rowspan=1, sticky=E + W + S + N, pady=4,
                        padx=80)
        self.entry.bind('<Return>', self.returnEnter)

        self.enter = Button(self, text="Enter", command=self.returnButton)
        self.enter.grid(row=self.textRow + 1, column=self.textColumn + 1)

        all_keys = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for press_key in all_keys:
            self.text.bind(press_key, self.textReturnEnter, add='')
            if self.OS != "windows":
                self.text.bind(f'<Control-Key-"{press_key}">', self.keepCurrent)
                self.text.bind(f'<Command-Key-"{press_key}">', self.keepCurrent)

        self.text.bind('<Control-Key-z>', self.backToHistory)

        self.text.bind('<Double-Button-1>', self.doubleLeftClick)
        self.text.bind('<ButtonRelease-1>', self.show_cursor_pos)
        self.text.bind('<KeyRelease>', self.show_cursor_pos)

        self.keymap_frame = KeyMapFrame(self, self.pressCommand)
        self.keymap_frame.grid(row=1, column=self.textColumn + 2, rowspan=self.keymap_frame.rows,
                               columnspan=2, padx=6, pady=6, sticky=NW)

        Label(self, text="Map Templates", foreground="blue") \
            .grid(row=self.keymap_frame.rows + 1, column=self.textColumn + 2, columnspan=2, rowspan=1, padx=10)
        self.configListBox = Combobox(self, values=getConfigList(), state='readonly')
        self.configListBox.grid(row=self.keymap_frame.rows + 2, column=self.textColumn + 2, columnspan=2, rowspan=1,
                                padx=6)
        # select current config file
        self.configListBox.set(self.configFile.split(os.sep)[-1])
        self.configListBox.bind('<<ComboboxSelected>>', self.on_select_configfile)

    def show_cursor_pos(self, event):
        cursor_index = self.text.index(INSERT)
        row, col = cursor_index.split('.')
        self.cursor_index_label.config(text=f"{row}:{col}")

    ## TODO: select entity by double left click
    def doubleLeftClick(self, event):
        if self.debug:
            print("Action Track: doubleLeftClick")
        pass
        # cursor_index = self.text.index(INSERT)
        # start_index = ("%s - %sc" % (cursor_index, 5))
        # end_index = ("%s + %sc" % (cursor_index, 5))
        # self.text.tag_add('SEL', '1.0',"end-1c")

    def toggle_use_recommend(self):
        if not self.use_recommend.get():
            content = self.text.get_text()
            content = removeRecommendContent(content, self.recommendRe)
            self.writeFile(self.fileName, content, '1.0')

    def onOpen(self):
        filename = filedialog.askopenfilename(
            filetypes=[('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')])
        if filename != '':
            self.text.delete("1.0", END)
            text = self.readFile(filename)
            self.text.insert(END, text)
            self.filename_lbl.config(text="File: " + filename)
            self.autoLoadNewFile(self.fileName, "1.0")
            self.text.mark_set(INSERT, "1.0")
            self.setCursorLabel(self.text.index(INSERT))

    def readFile(self, filename):
        f = open(filename)
        try:
            text = f.read()
            self.file_encoding = f.encoding
        except UnicodeDecodeError:
            f = open(filename, encoding='utf-8')
            text = f.read()
        self.fileName = filename
        return text

    def setFont(self, value):
        _family = self.textFontStyle
        _size = value
        _weight = "bold"
        _underline = 0
        fnt = font.Font(family=_family, size=_size, weight=_weight, underline=_underline)
        Text(self, font=fnt)

    def setCursorLabel(self, cursor_index):
        row, col = cursor_index.split('.')
        self.cursor_index_label.config(text=f"{row}:{col}")

    def returnButton(self):
        if self.debug:
            print("Action Track: returnButton")
        self.pushToHistory()
        # self.returnEnter(event)
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content

    def returnEnter(self, event):
        if self.debug:
            print("Action Track: returnEnter")
        self.pushToHistory()
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content

    def textReturnEnter(self, event):
        press_key = event.char
        if self.debug:
            print("Action Track: textReturnEnter")
        self.pushToHistory()
        print("event: ", press_key)
        self.clearCommand()
        self.executeCursorCommand(press_key.lower())
        return 'break'

    def backToHistory(self, event):
        if self.debug:
            print("Action Track: backToHistory")
        if len(self.history) > 0:
            content, cursor = self.history.pop()
            self.writeFile(self.fileName, content, cursor)
        else:
            print("History is empty!")

    def keepCurrent(self, event):
        if self.debug:
            print("Action Track: keepCurrent")
        print("keep current, insert:", INSERT)
        print("before:", self.text.index(INSERT))
        self.text.insert(INSERT, 'p')
        print("after:", self.text.index(INSERT))

    def clearCommand(self):
        if self.debug:
            print("Action Track: clearCommand")
        self.entry.delete(0, 'end')

    def executeCursorCommand(self, command):
        if self.debug:
            print("Action Track: executeCursorCommand")
        print("Command:" + command)
        try:
            cursor_index = self.text.index(SEL_LAST)
            aboveHalf_content = self.text.get('1.0', SEL_FIRST)
            followHalf_content = self.text.get(SEL_FIRST, "end-1c")
            selected_string = self.text.selection_get()
            if re.match(self.entity_regex, selected_string) != None:
                ## if have selected entity
                new_string_list = selected_string.strip('[@]').rsplit('#', 1)
                new_string = new_string_list[0]
                followHalf_content = followHalf_content.replace(selected_string, new_string, 1)
                selected_string = new_string
                # cursor_index = "%s - %sc" % (cursor_index, str(len(new_string_list[1])+4))
                cursor_index = cursor_index.split('.')[0] + "." + str(
                    int(cursor_index.split('.')[1]) - len(new_string_list[1]) + 4)
            afterEntity_content = followHalf_content[len(selected_string):]

            if command == "q":
                print('q: remove entity label')
            else:
                if len(selected_string) > 0:
                    entity_content, cursor_index = self.replaceString(selected_string, selected_string, command,
                                                                      cursor_index)
            aboveHalf_content += entity_content
            content = self.addRecommendContent(aboveHalf_content, afterEntity_content, self.use_recommend.get())
            content = content
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            ## not select text
            cursor_index = self.text.index(INSERT)
            [line_id, column_id] = cursor_index.split('.')
            aboveLine_content = self.text.get('1.0', str(int(line_id) - 1) + '.end')
            belowLine_content = self.text.get(str(int(line_id) + 1) + '.0', "end-1c")
            line = self.text.get(line_id + '.0', line_id + '.end')
            matched_span = (-1, -1)
            detected_entity = -1  ## detected entity type:－1 not detected, 1 detected gold, 2 detected recommend
            for match in re.finditer(self.entity_regex, line):
                if match.span()[0] <= int(column_id) & int(column_id) <= match.span()[1]:
                    matched_span = match.span()
                    detected_entity = 1
                    break
            if detected_entity == -1:
                for match in re.finditer(self.recommendRe, line):
                    if match.span()[0] <= int(column_id) & int(column_id) <= match.span()[1]:
                        matched_span = match.span()
                        detected_entity = 2
                        break
            line_before_entity = line
            line_after_entity = ""
            if matched_span[1] > 0:
                selected_string = line[matched_span[0]:matched_span[1]]
                if detected_entity == 1:
                    new_string, old_entity_type = selected_string.strip('[@*]').rsplit('#', 1)
                elif detected_entity == 2:
                    new_string, old_entity_type = selected_string.strip('[$*]').rsplit('#', 1)
                line_before_entity = line[:matched_span[0]]
                line_after_entity = line[matched_span[1]:]
                selected_string = new_string
                entity_content = selected_string
                cursor_index = line_id + '.' + str(int(matched_span[1]) - (len(old_entity_type) + 4))
                if command == "q":
                    print('q: remove entity label')
                elif command == 'y':
                    print("y: comfirm recommend label")
                    keydef = self.get_cmd_by_name(old_entity_type)
                    entity_content, cursor_index = self.replaceString(selected_string, selected_string, keydef.key,
                                                                      cursor_index)
                else:
                    if len(selected_string) > 0:
                        keydef = self.get_cmd_by_key(command)
                        if keydef is not None:
                            entity_content, cursor_index = self.replaceString(selected_string, selected_string, command,
                                                                              cursor_index)
                        else:
                            return
                line_before_entity += entity_content
            if aboveLine_content != '':
                aboveHalf_content = aboveLine_content + '\n' + line_before_entity
            else:
                aboveHalf_content = line_before_entity

            if belowLine_content != '':
                followHalf_content = line_after_entity + '\n' + belowLine_content
            else:
                followHalf_content = line_after_entity

            content = self.addRecommendContent(aboveHalf_content, followHalf_content, self.use_recommend.get())
            content = content
            self.writeFile(self.fileName, content, cursor_index)

    def executeEntryCommand(self, command):
        if self.debug:
            print("Action Track: executeEntryCommand")
        if len(command) == 0:
            currentCursor = self.text.index(INSERT)
            newCurrentCursor = str(int(currentCursor.split('.')[0]) + 1) + ".0"
            self.text.mark_set(INSERT, newCurrentCursor)
            self.setCursorLabel(newCurrentCursor)
        else:
            command_list = decompositCommand(command)
            for idx in range(0, len(command_list)):
                command = command_list[idx]
                if len(command) == 2:
                    select_num = int(command[0])
                    command = command[1]
                    content = self.text.get_text()
                    cursor_index = self.text.index(INSERT)
                    newcursor_index = cursor_index.split('.')[0] + "." + str(
                        int(cursor_index.split('.')[1]) + select_num)
                    # print "new cursor position: ", select_num, " with ", newcursor_index, "with ", newcursor_index
                    selected_string = self.text.get(cursor_index, newcursor_index)
                    aboveHalf_content = self.text.get('1.0', cursor_index)
                    followHalf_content = self.text.get(cursor_index, "end-1c")
                    keydef = self.get_cmd_by_key(command)
                    if keydef is not None:
                        if len(selected_string) > 0:
                            # print "insert index: ", self.text.index(INSERT) 
                            followHalf_content, newcursor_index = self.replaceString(followHalf_content,
                                                                                     selected_string, command,
                                                                                     newcursor_index)
                            content = self.addRecommendContent(aboveHalf_content, followHalf_content,
                                                               self.use_recommend.get())
                            # content = aboveHalf_content + followHalf_content
                    self.writeFile(self.fileName, content, newcursor_index)

    def replaceString(self, content, string, replaceType, cursor_index):
        cmd = self.get_cmd_by_key(replaceType)
        if cmd is not None:
            new_string = "[@" + string + "#" + cmd.name + "*]"
            row, col = cursor_index.split('.')
            newcursor_index = f"{row}.{int(col) + len(cmd.name) + 5}"
        else:
            print("Invaild command!")
            print("cursor index: ", self.text.index(INSERT))
            return content, cursor_index
        content = content.replace(string, new_string, 1)
        return content, newcursor_index

    def writeFile(self, fileName, content, newcursor_index):
        if self.debug:
            print("Action track: writeFile")

        if len(fileName) > 0:
            if ".ann" in fileName:
                new_name = fileName
                ann_file = open(new_name, 'w', encoding=self.file_encoding)
                ann_file.write(content)
                ann_file.close()
            else:
                new_name = fileName + '.ann'
                ann_file = open(new_name, 'w', encoding=self.file_encoding)
                ann_file.write(content)
                ann_file.close()
            self.autoLoadNewFile(new_name, newcursor_index)
        else:
            print("Don't write to empty file!")

    def addRecommendContent(self, train_data, decode_data, recommendMode):
        if not recommendMode:
            content = train_data + decode_data
        else:
            if self.debug:
                print("Action Track: addRecommendContent, start Recommend entity")
            content = maximum_matching(train_data, decode_data)
        return content

    def autoLoadNewFile(self, fileName, newcursor_index):
        if self.debug:
            print("Action Track: autoLoadNewFile")
        if len(fileName) > 0:
            self.text.delete("1.0", END)
            text = self.readFile(fileName)
            self.text.insert("end-1c", text)
            self.filename_lbl.config(text="File: " + fileName)
            self.text.mark_set(INSERT, newcursor_index)
            self.text.see(newcursor_index)
            self.setCursorLabel(newcursor_index)
            self.setColorDisplay()

    def setColorDisplay(self):
        countVar = StringVar()
        cursor_row, _ = self.text.index(INSERT).split('.')
        lineStart = cursor_row + '.0'
        lineEnd = cursor_row + '.end'

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
            pos = self.text.search(self.entity_regex, "matchEnd", "searchLimit", count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", f"{pos}+{countVar.get()}c")
            self.text.highlight_entity(pos, int(countVar.get()))
        ## color recommend type
        while True:
            recommend_pos = self.text.search(self.recommendRe, "recommend_matchEnd", "recommend_searchLimit",
                                             count=countVar, regexp=True)
            if recommend_pos == "":
                break
            self.text.mark_set("recommend_matchStart", recommend_pos)
            self.text.mark_set("recommend_matchEnd", f"{recommend_pos}+{countVar.get()}c")
            self.text.highlight_recommend(recommend_pos, int(countVar.get()))

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
            pos = self.text.search(self.insideNestEntityRe, "matchEnd", "searchLimit", count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            ledge_low = f"{pos} + 2c"
            redge_high = f"{pos} + {int(countVar.get()) - 1}c"
            self.text.tag_add("insideEntityColor", ledge_low, redge_high)

    def pushToHistory(self):
        self.history.append((self.text.get_text(), self.text.index(INSERT)))

    ## update shortcut map, directly in current configfile
    def renewPressCommand(self):
        if self.debug:
            print("Action Track: renewPressCommand")
        self.pressCommand = self.keymap_frame.read_keymap()
        with open(self.configFile, 'w') as fp:
            fp.write(str(self.pressCommand))
        self.keymap_frame.update_keymap(self.pressCommand)
        messagebox.showinfo("Remap Notification",
                            "Shortcut map has been updated!\n\n" +
                            "Configure file has been saved in File:" + self.configFile)

    ## save as new shortcut map
    def savenewPressCommand(self):
        if self.debug:
            print("Action Track: savenewPressCommand")
        self.pressCommand = self.keymap_frame.read_keymap()
        # prompt to ask configFile name
        self.configFile = filedialog.asksaveasfilename(
            initialdir="./configs/",
            title="Save New Config",
            filetypes=(("YEDDA configs", "*.config"), ("all files", "*.*")))
        # change to relative path following self.init()
        self.configFile = os.path.relpath(self.configFile)
        # make sure ending with ".config"
        if not self.configFile.endswith(".config"):
            self.configFile += ".config"
        with open(self.configFile, 'w') as fp:
            fp.write(str(self.pressCommand))
        self.keymap_frame.update_keymap(self.pressCommand)
        messagebox.showinfo("Save New Map Notification",
                            "Shortcut map has been saved and updated!\n\n"
                            + "Configure file has been saved in File:" + self.configFile)

    def on_select_configfile(self, event=None):
        if event and self.debug:
            print("Change shortcut map to: ", event.widget.get())
        self.configFile = os.path.join("configs", event.widget.get())
        self.keymap_frame.update_keymap(self.pressCommand)

    def getCursorIndex(self):
        return self.text.index(INSERT)

    def generateSequenceFile(self):
        if (".ann" not in self.fileName) and (".txt" not in self.fileName):
            out_error = "Export only works on filename ended in .ann or .txt!\nPlease rename file."
            print(out_error)
            messagebox.showerror("Export error!", out_error)
            return -1
        dlg = QueryExport(self, self.fileName, self.text.get_text()[:100])
        if not dlg.confirmed:
            print("Operation canceled")
            return
        fileLines = open(self.fileName, 'r').readlines()
        lineNum = len(fileLines)
        new_filename = self.fileName.split('.ann')[0] + '.anns'
        seqFile = open(new_filename, 'w')
        for line in fileLines:
            if len(line) <= 2:
                seqFile.write('\n')
                continue
            else:
                if not self.keepRecommend:
                    line = removeRecommendContent(line, self.recommendRe)
                wordTagPairs = getWordTagPairs(line, dlg.segmented(), dlg.tag_scheme(), dlg.only_NP(),
                                               self.goldAndrecomRe)
                for wordTag in wordTagPairs:
                    seqFile.write(wordTag)
                ## use null line to seperate sentences
                seqFile.write('\n')
        seqFile.close()
        print("Exported file into sequence style in file: ", new_filename)
        print("Line number:", lineNum)
        showMessage = "Exported file successfully!\n\n"
        showMessage += "Tag scheme: " + dlg.tag_scheme() + "\n\n"
        showMessage += "Keep Recom: " + str(self.keepRecommend) + "\n\n"
        showMessage += "Text Segmented: " + str(dlg.segmented()) + "\n\n"
        showMessage += "Line Number: " + str(lineNum) + "\n\n"
        showMessage += "Saved to File: " + new_filename
        messagebox.showinfo("Export Message", showMessage)

    def get_cmd_by_key(self, key):
        return next((item for item in self.pressCommand if item.key == key), None)

    def get_cmd_by_name(self, name):
        return next((item for item in self.pressCommand if item.name == name), None)


def getConfigList():
    fileNames = os.listdir("./configs")
    filteredFileNames = sorted(filter(lambda x: (not x.startswith(".")) and (x.endswith(".config")), fileNames))
    return list(filteredFileNames)


def getWordTagPairs(tagedSentence, segmented=True, tagScheme="BMES", onlyNP=False, entityRe=r'\[\@.*?\#.*?\*\]'):
    sentence = tagedSentence.strip('\n')
    tagged_chunks = []
    for match in re.finditer(entityRe, sentence):
        chunk = (match.group(), match.start(), match.end(), True)  # (chunk_of_words, start, end, is_tagged)
        tagged_chunks.append(chunk)

    if len(tagged_chunks) == 0:
        return [(sentence, 0, len(sentence), False)]

    chunks = []
    for idx in range(0, len(tagged_chunks)):
        if idx == 0:
            if tagged_chunks[idx][1] > 0:  # first character is not tagged
                chunks.append((sentence[0:tagged_chunks[idx][1]], 0, tagged_chunks[idx][1], False))
                chunks.append(tagged_chunks[idx])
            else:
                chunks.append(tagged_chunks[idx])
        else:
            if tagged_chunks[idx][1] == tagged_chunks[idx - 1][2]:
                chunks.append(tagged_chunks[idx])
            elif tagged_chunks[idx][1] < tagged_chunks[idx - 1][2]:
                print("ERROR: found pattern has overlap!", tagged_chunks[idx][1], ' with ', tagged_chunks[idx - 1][2])
            else:
                chunks.append(
                    (sentence[tagged_chunks[idx - 1][2]:tagged_chunks[idx][1]], tagged_chunks[idx - 1][2],
                     tagged_chunks[idx][1],
                     False))
                chunks.append(tagged_chunks[idx])

        sent_len = len(sentence)
        if idx == len(tagged_chunks) - 1:
            if tagged_chunks[idx][2] > sent_len:
                print("ERROR: found pattern position larger than sentence length!")
            elif tagged_chunks[idx][2] < sent_len:
                chunks.append([sentence[tagged_chunks[idx][2]:sent_len], tagged_chunks[idx][2], sent_len, False])
            else:
                continue
    return turnFullListToOutputPair(chunks, segmented, tagScheme, onlyNP)


def turnFullListToOutputPair(fullList, segmented=True, tagScheme="BMES", onlyNP=False):
    pair_list = []
    for chunk_words, start, end, is_tagged in fullList:
        if is_tagged:
            plain_words, label = chunk_words.strip('[@$]').rsplit('#', 1)
            label = label.strip('*')
            if segmented:
                plain_words = plain_words.split()
            if onlyNP:
                label = "NP"
            outList = outputWithTagScheme(plain_words, label, tagScheme)
            pair_list.extend(outList)
        else:
            if segmented:
                words = chunk_words.split()
            else:
                words = chunk_words  # actually chars
            for word_or_char in words:
                if word_or_char == ' ':
                    continue
                pair = word_or_char + ' ' + 'O\n'
                pair_list.append(pair)
    return pair_list


def outputWithTagScheme(input_list, label, tagScheme="BMES"):
    output_list = []
    list_length = len(input_list)
    if tagScheme == "BMES":
        if list_length == 1:
            pair = input_list[0] + ' ' + 'S-' + label + '\n'
            output_list.append(pair)
        else:
            for idx in range(list_length):
                if idx == 0:
                    pair = input_list[idx] + ' ' + 'B-' + label + '\n'
                elif idx == list_length - 1:
                    pair = input_list[idx] + ' ' + 'E-' + label + '\n'
                else:
                    pair = input_list[idx] + ' ' + 'M-' + label + '\n'
                output_list.append(pair)
    else:
        for idx in range(list_length):
            if idx == 0:
                pair = input_list[idx] + ' ' + 'B-' + label + '\n'
            else:
                pair = input_list[idx] + ' ' + 'I-' + label + '\n'
            output_list.append(pair)
    return output_list


def removeRecommendContent(content, recommendRe=r'\[\$.*?\#.*?\*\](?!\#)'):
    output_content = ""
    last_match_end = 0
    for match in re.finditer(recommendRe, content):
        matched = content[match.span()[0]:match.span()[1]]
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
            num_select = ''
    return command_list


def main():
    print("SUTDAnnotator launched!")
    print("OS:", platform.system())
    root = Tk()
    width, height = 1300, 700
    x = max((root.winfo_screenwidth() - width) // 2, 0)
    y = max((root.winfo_screenheight() - height) // 2, 0)
    root.geometry(f'{width}x{height}+{x}+{y}')
    app = Application(root)
    app.setFont(17)
    root.mainloop()


if __name__ == '__main__':
    main()
