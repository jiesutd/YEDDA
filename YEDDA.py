# -*- coding: utf-8 -*-
import os.path
import platform
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox
from collections import deque
from tkinter import *
from tkinter.ttk import Frame, Button, Radiobutton, Label, Combobox
from tkinter.simpledialog import Dialog
from tkinter.scrolledtext import ScrolledText
from dataclasses import dataclass
from typing import List, Optional, Tuple

from utils.recommend import *


class Editor(ScrolledText):
    def __init__(self, parent, entity_pattern, recommend_pattern):
        super().__init__(parent, selectbackground='light salmon')
        self.entity_pattern = entity_pattern
        self.recommend_pattern = recommend_pattern
        fnt = font.Font(family='Times', size=20, weight="bold", underline=0)
        self.config(insertbackground='red', insertwidth=4, font=fnt)

        def _ignore(_): return 'break'

        # Disable the default copy behaviour when right click.
        # For MacOS, right click is button 2, other systems are button3
        self.bind('<Button-2>', _ignore)
        self.bind('<Button-3>', _ignore)
        self.set_colors(None)

    def set_colors(self, colors: Optional[List[Tuple[str, str]]]):
        """
        Set colors for different entity type
        :param colors: list of (entity, color), or None to disable colorful annotation
        """
        self.colors = colors
        for t in self.tag_names():
            if t.startswith('entity') or t.startswith('recommend'):
                self.tag_delete(t)
        # TODO color edge to discriminate recommend
        self.tag_configure("edge", background="light grey", foreground='DimGrey', font=('Times', 12))
        if colors is None:
            self.tag_configure("recommend", background='light green')
            self.tag_configure("entity", background="SkyBlue1")
        else:
            for label, color in self.colors:
                self.tag_configure('entity_' + label, background=color)
                self.tag_configure('recommend_' + label, background=color)

    def _highlight_entity(self, start: str, count: int, tag_name: str):
        end = f'{start}+{count}c'
        sharp_pos = self.get(start, end).rfind('#')
        word_start = f"{start}+2c"
        word_end = f"{start}+{sharp_pos}c"
        if self.colors:
            label_start = f'{start}+{sharp_pos + 1}c'
            label_end = f'{start}+{count - 2}c'
            label = self.get(label_start, label_end)
            tag_name = f'{tag_name}_{label}'
        self.tag_add(tag_name, word_start, word_end)
        self.tag_add("edge", start, word_start)
        self.tag_add("edge", word_end, end)

    def show_annotation_tag(self, show: bool):
        self.tag_configure('edge', elide=not show)

    def highlight_recommend(self, start: str, count: int):
        self._highlight_entity(start, count, 'recommend')

    def highlight_entity(self, start: str, count: int):
        self._highlight_entity(start, count, 'entity')

    def get_text(self) -> str:
        """get text from 0 to end"""
        return self.get("1.0", "end-1c")

    def _highlight_entities(self, pattern, highlight_func):
        count_var = StringVar()
        from_index = '1.0'
        while True:
            pos = self.search(pattern, from_index, END, count=count_var, regexp=True)
            if pos == "":
                break
            from_index = f"{pos}+{count_var.get()}c"
            highlight_func(pos, int(count_var.get()))

    def update_view(self):
        self._highlight_entities(self.entity_pattern, self.highlight_entity)
        self._highlight_entities(self.recommend_pattern, self.highlight_recommend)

    def current_entity(self) -> (str, (str, int)):
        def find_pattern_span_in_line(pattern):
            row, col = self.index(INSERT).split('.')
            cursor_col = int(col)
            count_var = StringVar()
            from_index = f'{row}.0'
            while True:
                pos = self.search(pattern, from_index, f'{row}.end', count=count_var, regexp=True)
                if pos == '':
                    break
                row, col = pos.split('.')
                match_end = f'{row}.{int(col) + int(count_var.get())}'  # here don't use offset form
                if int(col) < cursor_col < (int(col) + int(count_var.get())):
                    return pos, match_end
                from_index = match_end
            return None

        span = find_pattern_span_in_line(self.entity_pattern)
        if span is not None:
            return 'gold', span
        span = find_pattern_span_in_line(self.recommend_pattern)
        if span is not None:
            return 'recommend', span
        else:
            return None, (None, None)

    def get_selection(self) -> Optional[str]:
        try:
            return self.selection_get()
        except TclError:
            return None


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

            name_entry = Entry(self, font=(self.textFontStyle, 14), bg=item.color)
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
        super().__init__(parent, 'Exporting ' + filename)  # here dialog shows

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
        self.export_recommended_var = BooleanVar(master, True)
        Checkbutton(master, text="Export Recommended", variable=self.export_recommended_var).pack()

    def apply(self):
        """override, called after press ok, not called on cancel"""
        self.confirmed = True

    def segmented(self) -> bool:
        return self.segmented_var.get()

    def only_NP(self) -> bool:
        return self.only_NP_var.get()

    def keep_recommended(self) -> bool:
        return self.export_recommended_var.get()

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


def all_colors():
    colors = []
    for color in ('LightBlue', 'LightCyan', 'LightGoldenrod', 'LightPink',
                  'LightSalmon', 'LightSkyBlue', 'LightSteelBlue', 'LightYellow'):
        colors += [c + n for c, n in zip([color] * 5, ['', '1', '2', '3', '4'])]
    return sorted(colors, key=lambda c: list(reversed(c)))


class Application(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.Version = "YEDDA-V1.0 Annotator"
        self.OS = platform.system().lower()
        self.fileName = ""
        self.file_encoding = 'utf-8'
        self.debug = False
        self.history = deque(maxlen=20)
        self.pressCommand = [KeyDef('a', "Artificial"),
                             KeyDef('b', "Event"),
                             KeyDef('c', "Fin-Concept"),
                             KeyDef('d', "Location"),
                             KeyDef('e', "Organization"),
                             KeyDef('f', "Person"),
                             KeyDef('g', "Sector"),
                             KeyDef('h', "Other")]
        for key, color in zip(self.pressCommand, all_colors()):
            key.color = color

        # default GUI display parameter
        self.textRow = max(len(self.pressCommand), 20)
        self.textColumn = 5

        self.configFile = "configs/default.config"
        self.entity_regex = r'\[\@.*?\#.*?\*\](?!\#)'
        self.recommendRe = r'\[\$.*?\#.*?\*\](?!\#)'
        self.goldAndrecomRe = r'\[[\@\$)].*?\#.*?\*\](?!\#)'
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
        self.text = Editor(self, self.entity_regex, self.recommendRe)
        self.text.grid(row=1, column=0, columnspan=self.textColumn, rowspan=self.textRow, padx=12, sticky=NSEW)

        btn = Button(self, text="Open", command=self.onOpen)
        btn.grid(row=1, column=self.textColumn + 1)
        btn = Button(self, text="ReMap", command=self.renewPressCommand)
        btn.grid(row=2, column=self.textColumn + 1, pady=4)
        btn = Button(self, text="NewMap", command=self.savenewPressCommand)
        btn.grid(row=3, column=self.textColumn + 1, pady=4)
        btn = Button(self, text="Export", command=self.generateSequenceFile)
        btn.grid(row=4, column=self.textColumn + 1, pady=4)

        self.use_recommend = BooleanVar(self, True)
        check = Checkbutton(self, text='Recommend', command=self.toggle_use_recommend, variable=self.use_recommend)
        check.grid(row=5, column=self.textColumn + 1, sticky=W, pady=4)

        show_tags_var = BooleanVar(self, True)
        check = Checkbutton(self, text='Show Tags', variable=show_tags_var,
                            command=lambda: self.text.show_annotation_tag(show_tags_var.get()))
        check.grid(row=6, column=self.textColumn + 1, sticky=W)

        self.use_colorful_var = BooleanVar(self, False)
        check = Checkbutton(self, text='Colorful', variable=self.use_colorful_var, command=self.toggle_use_colorful)
        check.grid(row=7, column=self.textColumn + 1, sticky=W)

        self.cursor_index_label = Label(self, text="Ln 1, Col 0")
        self.cursor_index_label.grid(row=self.textRow + 1, sticky=NSEW, pady=4, padx=4)
        cmd_var = StringVar()
        cmd_var.trace_add('write', lambda _, _1, _2: self.preview_cmd_range())
        self.entry = Entry(self, validate='focus', vcmd=self.preview_cmd_range, textvariable=cmd_var)
        self.entry.grid(row=self.textRow + 1, column=1, columnspan=self.textColumn - 2, sticky=NSEW, pady=4, padx=8)
        self.entry.bind('<FocusOut>', self.clear_preview_mark)
        self.entry.bind('<Return>', self.execute_command)

        btn = Button(self, text="Enter", command=lambda: self.execute_command(None))
        btn.grid(row=self.textRow + 1, column=self.textColumn - 1)

        all_keys = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for press_key in all_keys:
            self.text.bind(press_key, self.alphanum_key_pressed, add='')
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

        Label(self, text="KeyMap Templates:").grid(row=8, column=self.textColumn + 1)
        self.configListBox = Combobox(self, values=getConfigList(), state='readonly')
        self.configListBox.grid(row=8, column=self.textColumn + 2, columnspan=2)
        # select current config file
        self.configListBox.set(self.configFile.split(os.sep)[-1])
        self.configListBox.bind('<<ComboboxSelected>>', self.on_select_configfile)

    def show_cursor_pos(self, _):
        cursor_index = self.text.index(INSERT)
        row, col = cursor_index.split('.')
        self.cursor_index_label.config(text=f"Ln {row}, Col {col}")

    # TODO: select entity by double left click
    def doubleLeftClick(self, _):
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

    def toggle_use_colorful(self):
        if self.use_colorful_var.get():
            self.text.set_colors([(d.name, d.color) for d in self.pressCommand])
        else:
            self.text.set_colors(None)
        self.text.update_view()

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
            self.show_cursor_pos(None)

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
        self.cursor_index_label.config(text=f"Ln {row}, Col {col}")

    def clear_preview_mark(self, _):
        self.text.tag_delete('cmd-preview')

    def preview_cmd_range(self):
        preview_tag = 'cmd-preview'
        cmd = self.entry.get().strip()
        self.text.tag_delete(preview_tag)
        self.text.tag_configure(preview_tag, background='light salmon')
        match = re.match(r'^(-?[0-9]+).*', cmd)
        if match:
            count = int(match.group(1))
        else:
            count = 1
        if count > 0:
            self.text.tag_add(preview_tag, INSERT, f'{INSERT}+{count}c')
        else:
            self.text.tag_add(preview_tag, f'{INSERT}-{abs(count)}c', INSERT)
        return True

    def execute_command(self, _):
        self.pushToHistory()
        content = self.entry.get()
        self.clearCommand()
        self.execute_entry_command(content.strip())
        return content

    def alphanum_key_pressed(self, event):
        press_key = event.char
        self.pushToHistory()
        self.clearCommand()
        self.execute_cursor_command(press_key.lower())
        return 'break'

    def backToHistory(self, _):
        if self.debug:
            print("Action Track: backToHistory")
        if len(self.history) > 0:
            content, cursor = self.history.pop()
            self.writeFile(self.fileName, content, cursor)
        else:
            print("History is empty!")

    def keepCurrent(self, _):
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

    def execute_cursor_command(self, command):
        print("Command:" + command)
        found, (start, end) = self.text.current_entity()
        selected = self.text.get_selection()
        if not found and not selected:
            print(f'{command} outside entity, no selection, do nothing')
            return
        # selected whole entity, cursor just outside it
        selected_whole = selected is not None and \
                         (re.match(self.entity_regex, selected) or re.match(self.recommendRe, selected))

        # cursor outside existing entity & has selection
        if not found and selected is not None and not selected_whole:
            if self.get_cmd_by_key(command) is None:
                print(f'{command} key not bound, outside entity, do nothing')
                return
            cursor_index = self.text.index(SEL_LAST)
            entity_content, cursor_index = self.replaceString(selected, selected, command, cursor_index)
            above_half = self.text.get('1.0', SEL_FIRST) + entity_content
            below_half = self.text.get(SEL_LAST, "end-1c")
            content = self.addRecommendContent(above_half, below_half, self.use_recommend.get())
            self.writeFile(self.fileName, content, cursor_index)
        # Cursor inside existing entity, no matter has or not has selection.
        # Or Cursor outside existing entity (just on the edge), with the whole entity selected
        else:
            if selected_whole:
                start, end = self.text.index(SEL_FIRST), self.text.index(SEL_LAST)
            covered_string = self.text.get(start, end)
            old_entity, old_label = covered_string.strip('[@$*]').rsplit('#', 1)

            if command == "q":
                print('q: remove entity label')
                new_cursor = f'{end}-{5 + len(old_label)}c'
                entity_content = old_entity
            elif command == 'y':
                print("y: confirm recommend label")
                entity_content = f'[@{old_entity}#{old_label}*]'
                new_cursor = end
            elif len(old_entity) > 0 and self.get_cmd_by_key(command) is not None:
                print(f'{command}: change entity type')
                cmd = self.get_cmd_by_key(command)
                entity_content = f'[@{old_entity}#{cmd.name}*]'
                delta = len(cmd.name) - len(old_label)
                new_cursor = end + (f'+{delta}c' if delta >= 0 else f'{delta}c')
            else:
                print(f'{command}: key not bound, do nothing')
                return
            above_half = self.text.get('1.0', start) + entity_content
            below_half = self.text.get(end, 'end-1c')
            content = self.addRecommendContent(above_half, below_half, self.use_recommend.get())
            self.writeFile(self.fileName, content, new_cursor)

    def execute_entry_command(self, command):
        print(f"EntryCommand: {command}")
        if command == '':  # move to next line
            row, _ = self.text.index(INSERT).split('.')
            self.text.mark_set(INSERT, f'{int(row) + 1}.0')
            self.show_cursor_pos(None)
        elif command.isdigit():
            self.text.mark_set(INSERT, f'{INSERT}+{command}c')
            self.show_cursor_pos(None)
            self.preview_cmd_range()
        elif len(command) >= 2 and command[0] == '-' and command[1:].isdigit():
            self.text.mark_set(INSERT, f'{INSERT}{command}c')
            self.show_cursor_pos(None)
            self.preview_cmd_range()
        else:
            def split_commands(string):
                commands = []
                num = ''
                for c in string:
                    if c.isdigit():
                        num += c
                    else:
                        commands.append((int(num), c))
                        num = ''
                return commands

            for select_num, cmd in split_commands(command):
                assert select_num > 0
                sel_start = self.text.index(INSERT)
                sel_end = self.text.index(f'{INSERT}+{select_num}c')
                selected = self.text.get(sel_start, sel_end)
                if self.get_cmd_by_key(cmd) is not None:
                    above_half = self.text.get('1.0', sel_start)
                    below_half = self.text.get(sel_start, "end-1c")
                    below_half, new_cursor = self.replaceString(below_half, selected, cmd, sel_end)
                    content = self.addRecommendContent(above_half, below_half, self.use_recommend.get())
                    self.writeFile(self.fileName, content, new_cursor)

    def replaceString(self, content, string, replaceType, cursor_index):
        keydef = self.get_cmd_by_key(replaceType)
        if keydef is not None:
            new_string = "[@" + string + "#" + keydef.name + "*]"
            row, col = cursor_index.split('.')
            newcursor_index = f"{row}.{int(col) + len(keydef.name) + 5}"
            content = content.replace(string, new_string, 1)
            return content, newcursor_index
        else:
            print("Invalid command!")
            print("cursor index: ", self.text.index(INSERT))
            return content, cursor_index

    def writeFile(self, fileName, content, newcursor_index):
        print("writeFile")
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
            self.show_cursor_pos(None)
            self.text.update_view()

    def pushToHistory(self):
        self.history.append((self.text.get_text(), self.text.index(INSERT)))

    # update shortcut map, directly in current configfile
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

    # save as new shortcut map
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
        new_filename = self.fileName.split('.ann')[0] + '.' + dlg.tag_scheme().lower()
        seqFile = open(new_filename, 'w')
        for line in fileLines:
            if len(line) <= 2:
                seqFile.write('\n')
                continue
            else:
                if not dlg.keep_recommended():
                    line = removeRecommendContent(line, self.recommendRe)
                    pattern = self.entity_regex
                else:
                    pattern = self.goldAndrecomRe
                wordTagPairs = getWordTagPairs(line, dlg.segmented(), dlg.tag_scheme(), dlg.only_NP(), pattern)
                for wordTag in wordTagPairs:
                    seqFile.write(wordTag)
                # use null line to separate sentences
                seqFile.write('\n')
        seqFile.close()
        print("Exported file into sequence style in file: ", new_filename)
        print("Line number:", lineNum)
        showMessage = "Exported file successfully!\n\n"
        showMessage += "Tag scheme: " + dlg.tag_scheme() + "\n\n"
        showMessage += "Keep Recom: " + str(dlg.keep_recommended()) + "\n\n"
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
        tagged_chunks = [(sentence, 0, len(sentence), False)]  # TODO semantically wrong

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
