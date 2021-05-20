import sys
import webbrowser
from newspaper import Article
import spacy
import docx2txt
import os
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

from PyQt5 import uic, QtWidgets, QtCore


qtCreatorFile = "stackedwidgetVersion (spaCy + Bert).ui"
# nlp = spacy.load("en_core_web_lg")


class Ui(QtWidgets.QMainWindow):

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(qtCreatorFile, self)

        # change the program's main window name
        self.setWindowTitle('ArCo')

        # Online mode arrays
        # array for converting url to article title
        self.URLtoTitle = []  # title array
        self.SimilarityScore = []  # similarity score index
        self.SimilarityResult = []  # is it similar or not
        # (S = similar, SS = some similarity, NS = not similar)

        # Offline mode arrays
        self.filePath = []  # file path name

        # Online connect to other page buttons
        self.stackedWidget.setCurrentIndex(0)
        self.OnlineResultsBtn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        self.OnlineResultsBtn.clicked.connect(self.URL2Title)
        self.OnlineBackBtn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.OnlineBtn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.OnlineResultsBackBtn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        # Offline conenct to other page buttons
        self.OfflineBtn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))
        self.OfflineBackBtn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.OfflineSubmitBtn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(4))
        self.OfflineSubmitBtn.clicked.connect(self.Path2ComboBox)
        self.OfflineResultBackBtn.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(3))

        # Online other button functions
        self.OnlineAddBtn.clicked.connect(self.OnlineModeAdd)
        # sets enter key as add button as well.
        self.lineEdit.returnPressed.connect(self.OnlineAddBtn.click)
        self.OnlineDeleteBtn.clicked.connect(self.OnlineModeDel)
        self.OnlineViewBtn.clicked.connect(self.viewURL)
        self.OnlineModeResult.clicked.connect(self.OnlineSpacy)  # MAIN SPACY CODE
        self.OnlineSThreshold.clicked.connect(self.OnlineDefaultSBtn)
        self.OnlineSSThreshold.clicked.connect(self.OnlineDefaultSSBtn)

        self.OnlineSpacyOrBERT.addItem("spaCy")  # for spacy/BERT
        self.OnlineSpacyOrBERT.addItem("BERT")  # for spacy/BERT

        # Offline other button functions
        self.OfflineBrowseBtn.clicked.connect(self.ImportFiles)
        self.OfflineDelBtn.clicked.connect(self.OfflineModeDel)
        self.OfflineViewBtn.clicked.connect(self.viewFile)
        self.OfflineSThreshold.clicked.connect(self.OfflineDefaultSBtn)
        self.OfflineSSThreshold.clicked.connect(self.OfflineDefaultSSBtn)
        self.OfflineModeResult.clicked.connect(self.OfflineSpacy)

        self.OfflineSpacyOrBERT.addItem("spaCy")  # for spacy/BERT
        self.OfflineSpacyOrBERT.addItem("BERT")  # for spacy/BERT

        self.show()

    # FUNCTIONS FROM HERE ONWARDS
    # Online mode functions
    def OnlineModeAdd(self):
        url = self.lineEdit.text()
        print("url = ", url)
        if ("https://" not in url) and ("http://" not in url):
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Input valid URL with 'http://' or 'https://' in the text.")
            x = msg.exec_()  # need this line to show the msg box
        else:
            # only add link if never appear before
            out = self.OnlinelistWidget.findItems(url, QtCore.Qt.MatchExactly)
            if len(out) == 0:
                self.OnlinelistWidget.addItem(url)
        self.lineEdit.clear()

    def OnlineModeDel(self):
        listItems = self.OnlinelistWidget.selectedItems()
        if not listItems:
            return
        for item in listItems:
            self.OnlinelistWidget.takeItem(self.OnlinelistWidget.row(item))

    def viewURL(self):
        listItems = self.OnlinelistWidget.selectedItems()
        if not listItems:
            return
        for item in listItems:
            webbrowser.open(str(item.text()), new=2)

    def URL2Title(self):
        self.URLtoTitle.clear()
        self.OnlineMasterArticle.clear()
        listItems = [self.OnlinelistWidget.item(i).text()
                     for i in range(self.OnlinelistWidget.count())]
        # print("inside list widget=", listItems)
        for item in listItems:
            article = Article(str(item))
            article.download()
            article.parse()
            title = article.title
            print("article title=", title)
            self.URLtoTitle.append(title)
        print("URLtoTitle =", self.URLtoTitle)
        # add the title array to the dropbox
        self.OnlineMasterArticle.addItems(self.URLtoTitle)

    def OnlineSpacy(self):
        # select the model according to the combobox
        if str(self.OnlineSpacyOrBERT.currentText()) == "spaCy":
            nlp = spacy.load("en_core_web_lg")
            # print("combobox= spacy")
        elif str(self.OnlineSpacyOrBERT.currentText()) == "BERT":
            nlp = spacy.load("en_trf_bertbaseuncased_lg")
            # print("combobox= BERT")

        # clear the arrays everytime result btn is clicked
        self.SimilarityScore.clear()
        self.SimilarityResult.clear()

        # for if the user never enter any url
        if self.URLtoTitle == []:
            return

        # for changing the thresholds of Similar and Some Similarity types
        SThreshold = float(self.OnlineSLineEdit.text())
        SSThreshold = float(self.OnlineSSLineEdit.text())
        # if the user enter wrong value
        if SSThreshold >= SThreshold:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("S Threshold should be larger than SS Threshold")
            x = msg.exec_()  # need this line to show the msg box
            return

        # print(self.OnlineMasterArticle.currentIndex())
        doc1 = ""  # clear doc1
        doc2 = ""  # clear doc2
        MainURL = str(self.OnlinelistWidget.item(self.OnlineMasterArticle.currentIndex()).text())
        print("selected URL = ", MainURL)
        article = Article(MainURL)
        article.download()
        article.parse()
        doc1 = article.text
        # print("doc1: ", doc1)

        # do pre-processing when spacy model selected
        result1 = ""  # in case inside got stuff
        result2 = ""  # in case inside got stuff
        process1 = ""  # all here during bebugging and i am too lazy to remove it after
        process2 = ""
        pro_doc1 = ""
        pro_doc2 = ""
        result_1 = []
        result_2 = []
        if str(self.OnlineSpacyOrBERT.currentText()) == "spaCy":
            print("SPACY PREPROSSING")
            process1 = nlp(doc1.lower())
            for token in process1:
                if token.text in nlp.Defaults.stop_words:
                    continue
                if token.is_punct:
                    continue
                if token.lemma_ == "-PRON-":
                    continue
                # if token.text == "advertisement":  # newly added since got "advertisement" when testing
                #     continue
                result_1.append(token.lemma_)
            result1 = " ".join(result_1)
        else:  # for when BERT is selected
            result1 = doc1
        pro_doc1 = nlp(result1)
        print("pro_doc1: ", pro_doc1)

        for i in range(self.OnlinelistWidget.count()):
            if i != int(self.OnlineMasterArticle.currentIndex()):
                result_2.clear()  # clear result2 array
                url = self.OnlinelistWidget.item(i).text()
                article = Article(url)
                article.download()
                article.parse()
                doc2 = article.text
                # print("doc2: ", doc2)
                # do pre-processing when spacy model selected
                if str(self.OnlineSpacyOrBERT.currentText()) == "spaCy":
                    print("SPACY PREPROSSING")
                    process2 = nlp(doc2.lower())
                    for token in process2:
                        if token.text in nlp.Defaults.stop_words:
                            continue
                        if token.is_punct:
                            continue
                        if token.lemma_ == "-PRON-":
                            continue
                        # if token.text == "advertisement":  # newly added since got "advertisement" when testing
                        #     continue
                        result_2.append(token.lemma_)
                    result2 = " ".join(result_2)
                else:  # for when BERT is selected
                    result2 = doc2
                pro_doc2 = nlp(result2)
                print("pro_doc2: ", pro_doc2)

                Similarity = pro_doc1.similarity(pro_doc2)
                print(Similarity)
                self.SimilarityScore.append(Similarity)

                if Similarity >= SThreshold:
                    self.SimilarityResult.append("S")
                elif Similarity < SSThreshold:
                    self.SimilarityResult.append("NS")
                else:
                    self.SimilarityResult.append("SS")
            else:
                result_2.clear()  # clear result2 array

        # Table portion to show title, results and score
        table = self.OnlineTableWidget
        table.setColumnCount(3)
        table.setRowCount(self.OnlinelistWidget.count() - 1)
        # print(".count = ", self.OnlinelistWidget.count())
        table.setHorizontalHeaderLabels(['Article Title', 'Result', 'Similarity Score'])
        table.setColumnWidth(0, 650)

        y = 0
        for x in range(0, self.OnlinelistWidget.count() - 1):
            if x == self.OnlineMasterArticle.currentIndex():
                print("same article")
                y = x + 1
                table.setItem(x, 0, QtWidgets.QTableWidgetItem(str(self.URLtoTitle[y])))
                table.setItem(x, 1, QtWidgets.QTableWidgetItem(str(self.SimilarityResult[x])))
                table.setItem(x, 2, QtWidgets.QTableWidgetItem(str(self.SimilarityScore[x])))
                y = y + 1
            else:
                table.setItem(x, 0, QtWidgets.QTableWidgetItem(str(self.URLtoTitle[y])))
                table.setItem(x, 1, QtWidgets.QTableWidgetItem(str(self.SimilarityResult[x])))
                table.setItem(x, 2, QtWidgets.QTableWidgetItem(str(self.SimilarityScore[x])))
                y = y + 1

    def OnlineDefaultSBtn(self):
        self.OnlineSLineEdit.setText("0.960135")

    def OnlineDefaultSSBtn(self):
        self.OnlineSSLineEdit.setText("0.9286")

    # Offline mode functions
    def ImportFiles(self):
        self.filePath.clear()
        filePathName, _ = QtWidgets.QFileDialog.getOpenFileNames(
            # replace '' with QtCore.QDir.rootPath() if want to start from root directory
            self, 'Browse', '', "Files (*.txt *.pdf *.docx)")
        # The above code gets the path to the text
        # print("imported file path = ", filePathName)
        for i in range(0, len(filePathName)):
            out = self.OfflineListWidget.findItems(filePathName[i], QtCore.Qt.MatchExactly)
            if len(out) == 0:
                self.OfflineListWidget.addItem(filePathName[i])
                self.filePath.append(filePathName[i])

    def OfflineModeDel(self):
        listItems = self.OfflineListWidget.selectedItems()
        if not listItems:
            return
        for item in listItems:
            self.OfflineListWidget.takeItem(self.OfflineListWidget.row(item))

    def viewFile(self):
        listItems = self.OfflineListWidget.selectedItems()
        if not listItems:
            return
        for item in listItems:
            os.startfile(str(item.text()))

    def Path2ComboBox(self):
        self.filePath.clear()
        self.OfflineMasterArticle.clear()
        listItems = [self.OfflineListWidget.item(i).text()
                     for i in range(self.OfflineListWidget.count())]
        # print("inside list widget=", listItems)
        for item in listItems:
            self.filePath.append(item)
        print("file path name =", self.filePath)
        # add the title array to the dropbox
        self.OfflineMasterArticle.addItems(self.filePath)

    def OfflineDefaultSBtn(self):
        self.OfflineSLineEdit.setText("0.960135")

    def OfflineDefaultSSBtn(self):
        self.OfflineSSLineEdit.setText("0.9286")

    def OfflineSpacy(self):
        # select the model according to the combobox
        if str(self.OfflineSpacyOrBERT.currentText()) == "spaCy":
            nlp = spacy.load("en_core_web_lg")
        elif str(self.OfflineSpacyOrBERT.currentText()) == "BERT":
            nlp = spacy.load("en_trf_bertbaseuncased_lg")

        # clear the arrays everytime result btn is clicked
        self.SimilarityScore.clear()
        self.SimilarityResult.clear()

        # for if the user never enter any url
        if self.filePath == []:
            return

        # for changing the thresholds of Similar and Some Similarity types
        SThreshold = float(self.OfflineSLineEdit.text())
        SSThreshold = float(self.OfflineSSLineEdit.text())
        # if the user enter wrong value
        if SSThreshold >= SThreshold:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("S Threshold should be larger than SS Threshold")
            x = msg.exec_()  # need this line to show the msg box
            return

        doc1 = ""  # clear doc1
        MainFile = str(self.OfflineListWidget.item(self.OfflineMasterArticle.currentIndex()).text())
        print("selected URL = ", MainFile)
        if ".txt" in MainFile.lower():  # if Main text is txt file
            with open(MainFile, 'r') as ft:
                doc1 = ft.read()
        elif ".pdf" in MainFile.lower():  # if Main text is pdf file
            text_arr = []
            text_arr.clear()
            PDF_file = MainFile
            pages = convert_from_path(
                PDF_file, 500, poppler_path=r"D:\STUDIES\VIP\poppler-0.90.1\bin")
            image_counter = 1
            for page in pages:
                filename = "page_"+str(image_counter)+".jpg"
                page.save(filename, 'JPEG')  # creates a jpg of the page
                image_counter = image_counter + 1
            filelimit = image_counter-1  # total number of pages
            for i in range(1, filelimit + 1):
                filename = "page_"+str(i)+".jpg"
                text = str(((pytesseract.image_to_string(Image.open(filename)))))
                text_arr.append(text.replace('-\n', ''))  # due to truncation having a '-'
            doc1 = " ".join(text_arr)
            image_counter = 1  # this part onwards to remove the jpgs
            for page in pages:
                filename = "page_"+str(image_counter)+".jpg"
                os.remove(filename)
                image_counter = image_counter + 1
        elif ".docx" in MainFile.lower():
            doc1 = docx2txt.process(MainFile)
        print("doc1: ", doc1)

        # do pre-processing when spacy model selected
        result1 = ""  # in case inside got stuff
        result2 = ""  # in case inside got stuff
        process1 = ""  # all here during bebugging and i am too lazy to remove it after
        process2 = ""
        pro_doc1 = ""
        pro_doc2 = ""
        result_1 = []
        result_2 = []
        if str(self.OfflineSpacyOrBERT.currentText()) == "spaCy":
            process1 = nlp(doc1.lower())
            for token in process1:
                if token.text in nlp.Defaults.stop_words:
                    continue
                if token.is_punct:
                    continue
                if token.lemma_ == "-PRON-":
                    continue
                result_1.append(token.lemma_)
                result1 = " ".join(result_1)
        else:  # for when BERT is selected
            result1 = doc1
        pro_doc1 = nlp(result1)

        doc2 = ""  # clear doc2
        for i in range(self.OfflineListWidget.count()):
            if i != int(self.OfflineMasterArticle.currentIndex()):
                result_2.clear()  # clear result2 array
                File = self.OfflineListWidget.item(i).text()
                if ".txt" in File.lower():  # if test text is txt file
                    with open(File, 'r') as ft:
                        doc2 = ft.read()
                elif ".pdf" in File.lower():  # if test text is pdf file
                    text_arr = []
                    PDF_file = File
                    pages = convert_from_path(
                        PDF_file, 500, poppler_path=r"D:\STUDIES\VIP\poppler-0.90.1\bin")
                    image_counter = 1
                    for page in pages:
                        filename = "page_"+str(image_counter)+".jpg"
                        page.save(filename, 'JPEG')  # creates a jpg of the page
                        image_counter = image_counter + 1
                    filelimit = image_counter-1  # total number of pages
                    for i in range(1, filelimit + 1):
                        filename = "page_"+str(i)+".jpg"
                        text = str(((pytesseract.image_to_string(Image.open(filename)))))
                        text_arr.append(text.replace('-\n', ''))  # due to truncation having a '-'
                    doc2 = " ".join(text_arr)
                    image_counter = 1  # this part to remove the jpgs
                    for page in pages:
                        filename = "page_"+str(image_counter)+".jpg"
                        os.remove(filename)
                        image_counter = image_counter + 1
                elif ".docx" in File.lower():  # if test text is microsoft word file
                    doc2 = docx2txt.process(File)
                print("doc2: ", doc2)
                # do pre-processing when spacy model selected
                if str(self.OfflineSpacyOrBERT.currentText()) == "spaCy":
                    process2 = nlp(doc2.lower())
                    for token in process2:
                        if token.text in nlp.Defaults.stop_words:
                            continue
                        if token.is_punct:
                            continue
                        if token.lemma_ == "-PRON-":
                            continue
                        result_2.append(token.lemma_)
                        result2 = " ".join(result_2)
                else:  # for when BERT is selected
                    result2 = doc2
                pro_doc2 = nlp(result2)
                # print("pro_doc2: ", pro_doc2)

                Similarity = pro_doc1.similarity(pro_doc2)
                print(Similarity)
                self.SimilarityScore.append(Similarity)

                if Similarity >= SThreshold:
                    self.SimilarityResult.append("S")
                elif Similarity < SSThreshold:
                    self.SimilarityResult.append("NS")
                else:
                    self.SimilarityResult.append("SS")
            else:
                result_2.clear()  # clear result2 array

        # Table portion to show title, results and score
        table = self.OfflineTableWidget
        table.setColumnCount(3)
        table.setRowCount(self.OfflineListWidget.count() - 1)
        table.setHorizontalHeaderLabels(['Article Title', 'Result', 'Similarity Score'])
        table.setColumnWidth(0, 650)

        y = 0
        for x in range(0, self.OfflineListWidget.count() - 1):
            if x == self.OfflineMasterArticle.currentIndex():
                print("same article")
                y = x + 1
                table.setItem(x, 0, QtWidgets.QTableWidgetItem(str(self.filePath[y])))
                table.setItem(x, 1, QtWidgets.QTableWidgetItem(str(self.SimilarityResult[x])))
                table.setItem(x, 2, QtWidgets.QTableWidgetItem(str(self.SimilarityScore[x])))
                y = y + 1
            else:
                table.setItem(x, 0, QtWidgets.QTableWidgetItem(str(self.filePath[y])))
                table.setItem(x, 1, QtWidgets.QTableWidgetItem(str(self.SimilarityResult[x])))
                table.setItem(x, 2, QtWidgets.QTableWidgetItem(str(self.SimilarityScore[x])))
                y = y + 1


app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()
