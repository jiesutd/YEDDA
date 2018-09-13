YEDDA: A Lightweight Collaborative Text Span Annotation Tool
======

About:
====
YEDDA (previously SUTDAnnotator) is developed for annotating chunk/entity/event
on text (almost all languages including English, Chinese), symbols, even emoji.

It supports shortcut annotation which makes it extremely efficient to annotate
text by hand. The user needs only select a text span and press a shortcut key,
the span will be annotated automatically. It also supports command annotation
model for annotating multiple entities in a single batch, as well as exporting
annotated text into sequence text.

Intelligent recommendation and administrator analysis is also included in the
updated version. It is compatible with all mainstream operating systems, such
as Windows, Linux, and MacOS.

For more details, please refer to [our paper (ACL2018:demo)][arxiv].

This GUI annotation tool is developed with the tkinter package and Python 2.7.

Author: [Jie Yang](https://jiesutd.github.io), Phd Candidate of SUTD.

Interface:
====
It provides both an annotator interface for efficient annotation and an admin
interface for result analysis.

* Annotator Interface:
 ![alt text](/EnglishInterface.png "English Interface demo")
 ![alt text](/ChineseInterface.png "Chinese Interface demo")
* Administrator Interface:
 ![alt text](/AdminInterface.png "Administrator Interface demo")

Use as an annotator
====
* Start the interface: run `python YEDDA_Annotator.py`.
* Configure a shortcut map on the right side of the annotation interface. Leave
  other labels empty if you don't need them, e.g. `a: Action; b: Loc; c: Cont`
* Click the `ReMap` button to store the map setting.
* Click `Open` button and select your input file. (Use the `.txt` or `.ann` file
  endings if you like)

YEDDA supports two annotation methods: (output format `[@text span＃Location*]`):
* Shortcut Key Annotation: select the text and press the corresponding shortcut
  (e.g. `c` for label `Cont`).
* Command Line Annotation: type the code at command entry (at the bottom of the
  annotation interface). For example, type `2c3b1a` end with `<Enter>`, it will
  annotate the following `2` characters as type `c: Cont`, the next `3` characters
  as type `b: Loc`, then the following `1` character as `a: Action`.

Intelligent recommendation:
* Intelligent recommendation is toggled by the `RMOn` and `RMOff` buttons.
* If recommendation model is enabled, system will recommend entities based on
  the annotated text. The Recommended span appears as `[$text span＃Location*]`
  in green color. (Note that the annotated span starts with `[@`, while the
  recommended span starts with `[$`).

The annotated results will be stored synchronously. Annotated file is located
at the same directory as the original file with the name of ***"original name
+ .ann"***

Use as an administrator
====
YEDDA provides a simple interface for an administrator to evaluate and analyze
annotation quality among multiple annotators. After collecting multiple annotated
`*.ann` files from multiple annotators (annotated on same plain text), YEDDA can
offer two toolkits to monitor the annotation quality: multi-annotator analysis
and pairwise annotator comparison.

* Start the interface: run `python YEDDA_Admin.py`
* Multi-Annotator Analysis: press button `Multi-Annotator Analysis` and select
  multiple annotated `*.ann` files, it will give f-measure matrix among all
  annotators. The result matrix is shown below:

  ![alt text](https://github.com/jiesutd/SUTDAnnotator/blob/master/resultMatrix.png "Result Matrix")

* Pairwise Annotators Comparison: press button `Pairwise Comparison` and select
  two annotated `*.ann` files, it will generate a specific comparison report
  (in `.tex` format, can be compiled as `.pdf` file). The demo pdf file is shown
  below:

  ![alt text](https://github.com/jiesutd/SUTDAnnotator/blob/master/detailReport.png "Detail Report")


Important features:
=====
1. Typing `Ctrl + Z` will undo the most recent modification
2. With the cursor inside an entity span, pressing a shortcut key (e.g. `x`)
   will update the label (bound with `x`) of the entity where cursor is. (`q`
   will remove the label)
3. Selecting the annotated text, such as `[@美国＃Location*]`, then pressing
   `q`, will restore the annotated text to its unannotated state (i.e. "美国").
4. Confirm or remove recommended entity: put cursor inside of the entity span
   and press `y` (yes) or `q` (quit).
5. In the command entry, just type `Enter` without any command, the cursor in
   text will move to the head of next line. (You can monitor this with "Cursor").
6. "Cursor" shows the current cursor position, with the row and column number
   represented in `row` and `col` respectively.
7. The "Export" button will export the ***".ann"*** file as a sequence file,
   ***".anns"***, in the same directory. In the source code, the `self.seged`
   flag controls the export behaviour. If your sentences consist of words
   separated with spaces (such as segmented Chinese and English), then you may
   set it to `True`, otherwise set it to `False` (for sentences consisting of
   characters without spaces, such as unsegmented Chinese text). Another flag
   `self.tagScheme` controls the export format, the exported ***".anns"*** will
   use the `BMES` format if this flag is set to `"BMES"`, otherwise the file is
   formatted as `"BIO".`


Cite: 
========
If you use YEDDA for research, please cite our [ACL paper](https://arxiv.org/pdf/1711.03759.pdf)
as follows:

    @article{yang2017yedda,  
     title={YEDDA: A Lightweight Collaborative Text Span Annotation Tool},  
     author={Yang, Jie and Zhang, Yue and Li, Linwei and Li, Xingxuan},  
     booktitle={Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics},
     url={http://aclweb.org/anthology/P18-4006},
     year={2018}  
    } 


Updating...
====
* 2018-May-07, Repository is renamed as YEDDA now!
* 2018-May-01, Our paper has been accepted as a demonstration at ACL 2018.
* 2017-Sep-27, (YEDDA V 1.0): project was officially named as YEDDA ! See our paper [here](https://arxiv.org/pdf/1711.03759.pdf).
* 2017-June-24, (V 0.6): support nested coloring; add event annotation beta version [Event_beta.py](Event_beta.py)
* 2017-May-31, (V 0.6): optimize for Windows OS.
* 2017-Apr-26, (V 0.5.3): fix bug with line merge when change entity type.
* 2017-Apr-20, (V 0.5.2): fix bugs with `newline` problem on MacOS/Linux/Windows. (`\r` `\n` `\r\n`)
* 2017-Apr-20, (V 0.5.1): change entity label more directly; optimize cursor figure.
* 2017-Apr-19, (V 0.5): update entity represent as `[@Entity#Type*]`; support change label directly; fix some bugs.
* 2017-Apr-15, (V 0.4): update example and readme.
* 2017-Apr-13, (V 0.4): modify color; support setting color single line or whole file (may be slow in large file) (`self.colorAllChunk`).
* 2017-Apr-12, (V 0.4): support BMES/BIO export (`self.tagScheme`); support segmented sentence export(`self.seged`); can save previous shortcut setting.
* 2016-Mar-01, (V 0.3): fix export bug (bug: set space when sentence didn't include any effective label).
* 2016-Jan-11, (V 0.2): add sequence format export function.
* 2016-Jan-09, (V 0.1): init version.

[arxiv]: https://arxiv.org/pdf/1711.03759.pdf
