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
Just run the .py file.
* Set your shortcut map in the right side of annotation interface, you can set other labels empty if the shortcut number is enough. For example: ***"a == ACTION, c == CONT"***
* Click the ***"Update map"*** button to store the map setting
* Click ***"Open"*** button and select your annotate file. (You may set your file name ended with .txt if possible)

This tool supports two ways of annotation:
* Select the text and press the corresponding shortcut (i.e. `a` for label ***"Action"***).
* Type the code at command line (at the bottom of the interface). For example, type `2a3c1a` end with `<Enter>`, it will annotate the following `2` character as type ***'a'(ACTION)***, the following `3` character as type ***'c'(CONT)***, then the following `1` character as  ***'a'(ACTION)***.

The annotated results will be stored synchronously. Annotated file is located at the same directory with origin file with the name of ***"origin name + .ann"***


Other features:
=====
* Type `ctrl + z` will undo  the most recent modification
* Selected the annotated text, such as "[美国＃CONT*]", then press `q`, the annotated text will be recoverd to unannotate format (i.e. "美国").
* In the command entry, just type `Enter` without any command, the cursor in text will move to the head of next line. (You can monitor this through "Cursor").
* The "Cursor" shows the current cursor position in text widget. `1.12+9c` means the `1st` line `12th` characters add with `9` character, which equals the `1st` line `21th` characters.
* `Export` button will export the ***".ann"*** file as a identity name with ***".anns"*** in the same directory. The exported file list the content in sequence format (We set label ***"MISC"*** as ***"O"*** in default, user can change it in the source code).


Updating...
====
* 2016-Jan-09: init version
* 2016-Jan-11: add sequence format export function