SUTDAnnotator: An efficient corpus annotation tool
======

About:
====
This GUI annotation tool is developed with tkinter package in Python. 

System required: Python 2.7

Interface demo:
![alt text](https://github.com/jiesutd/AnnTool/blob/master/EnglishInterface.png "English Interface demo")
![alt text](https://github.com/jiesutd/AnnTool/blob/master/ChineseInterface.png "Chinese Interface demo")

How to use?
====
Just run the .py file. `python SUTDAnnotator.py`
* Set your shortcut map in the right side of annotation interface, you can leave other labels empty if the shortcut number is enough. For example: `a: Action; c: Cont`
* Click the `Update map` button to store the map setting
* Click `Open` button and select your input file. (You may set your file name ended with .txt or .ann if possible)

This tool supports two ways of annotation:
* Select the text and press the corresponding shortcut (i.e. `c` for label `Cont`).
* Type the code at command line (at the bottom of the interface). For example, type `2c3b1a` end with `<Enter>`, it will annotate the following `2` character as type `c: Cont`, the following `3` character as type `b: Loc`, then the following `1` character as  `a: Action`.

The annotated results will be stored synchronously. Annotated file is located at the same directory with origin file with the name of ***"origin name + .ann"***


Important features:
=====
1. Type `ctrl + z` will undo  the most recent modification
2. Put cursor within an entity span, press shortcut key (e.g. `x`) to update label (binded with `x`) of the entity where cursor is belonging. (`q` for remove the label)
3. Selected the annotated text, such as "[@美国＃Location\*]", then press `q`, the annotated text will be recoverd to unannotate format (i.e. "美国").
4. Change label directly, such as select "[@美国＃Location\*]", then press `x`, the annotated text will change to new label mapped with shortcut `x` (e.g. "[@美国#Organization\*]").
5. In the command entry, just type `Enter` without any command, the cursor in text will move to the head of next line. (You can monitor this through "Cursor").
6. The "Cursor" shows the current cursor position in text widget, with `row` and `col` represent the row and column number, respectively.
7. `Export` button will export the ***".ann"*** file as a identity name with ***".anns"*** in the same directory. The exported file list the content in sequence format.


Updating...
====
* 2017-Apr-20, (V 0.5.2): fix bugs with `newline` problem on MacOS/Linux/Windows. (`\r``\n``\r\n`)
* 2017-Apr-20, (V 0.5.1): change entity label more directly; optimize cursor figure.
* 2017-Apr-19, (V 0.5): update entity represent as [@Entity#Type*]; support change label directly; fix some bugs.
* 2017-Apr-15, (V 0.4): update example and readme.
* 2017-Apr-13, (V 0.4): modify color; support setting color single line or whole file (may be slow in large file) (`self.colorAllChunk`).
* 2017-Apr-12, (V 0.4): support BMES/BIO export (`self.tagScheme`); support segmented sentence export(`self.seged`); can save previous shortcut setting.
* 2016-Mar-01, (V 0.3): fix export bug (bug: set space when sentence didn't include any effective label).
* 2016-Jan-11, (V 0.2): add sequence format export function.
* 2016-Jan-09, (V 0.1): init version.

