import sys, os, getopt, re
import preamble, auxiliary, style_tex
from subprocess import call
current_version = sys.version_info
import pyPdf

"""This function is used to create the tex file that is the songbook"""
class SongBooklet:
	
	def __init__(self, name, style, logo, indexing):
		
		self.makeDirs() # Generate used directories
		
		# Stored for later use
		self.name = name
		self.indexing = indexing
		
		# Translates the specified style to the name of an existing one
		self.style = auxiliary.search_styles(style)
		
		# Creates the preamble of the tex file
		self.texPreamble = preamble.create_preamble(name, self.style, logo)
		
		# Retrieves the songs in the folder
		self.songLst = self.getSongs()


	def makeBooklet(self):
		
		self.makeIndex() # Generates the index file
		
		# Addes the songs to the preamble and generates the pdf
		# The reason to generate the pdf multiple times is to make the internal latex references work
		tex = self.makePDF("***SONGS***", self.songsToString(), self.texPreamble)
		
		# If the special conditions of songs aren't satisfied the pdf is generated again with tweeked parameters
		if(not self.varifyIntegrity()):
			tex = self.makePDF("***SONGS***", self.songsToString(), self.texPreamble)
		
		# Generates the final pdf booklet
		self.makePDF("%***BOOKLET***", "", tex)
		
		# Moves the pdf to the folder named "Booklet"
		if(os.path.isfile("temp/" + "SongBook-" + self.name + ".pdf")):
			os.replace("temp/" + "SongBook-" + self.name + ".pdf", "Booklet/" + "SongBook-" + self.name + ".pdf")


	def makePDF(self, replace, string, tex):
		tex = self.addString(replace, string, tex)
		self.compilePDF()
		return tex
		

	def compilePDF(self):
		call(["pdflatex", "-output-directory", "temp/", "-jobname", "SongBook-" + self.name, "temp/SongBooklet.tex"])


	def varifyIntegrity(self):
		f = open("temp/SongBook-" + self.name + ".pdf", "rb")
		pdf = pyPdf.PdfFileReader(f)
		
		inconsistency = False
		for song in self.songLst:
			if("page" in song["options"]):
				song["options"]["pagebool"] = self.isSongOnPage(song["title"], song["options"]["page"], pdf.pages)
				if(not song["options"]["pagebool"]):
					inconsistency = True
					
		f.close()
		return not inconsistency
		

	def isSongOnPage(self, title, pageNum, pages):
		boolean = False
		index = 0
		for page in pages:
			if(index < len(pages) - 1):
				if(re.search("\d+" + title.replace(" ", ""), page.extractText())): # if page contains the song
					if(re.search(str(pageNum) + "$", page.extractText()) != None): # if page ends with the expected page number
						boolean = True
			index += 1
		return boolean
		

	def getSongs(self):
		specialSongs = []
		songs = []
		for file in os.listdir("Songs/"):
			if(file.endswith(".txt")):
				song = self.fileRead("Songs/" + file)
				line0 = song[:song.find("\n")]
				options = line0[:line0.find("\\")]
				title = re.search('(?<=song{)(.*?)}', line0)
				if(title != None):
					title = title.group(1)
					if(options != ""):
						specialSongs.append({"title" : title, "text" : song[song.find("\\"):], "options" : eval(options)})
					else:
						songs.append({"title" : title, "text" : song[song.find("\\"):], "options" : {}})
		
		sortedSpecialSongs = sorted(specialSongs, key = lambda song: self.comparFun(song))
		for song in sortedSpecialSongs:
			index = self.comparFun(song, -1)
			if(index == -1):
				index = len(songs)
			elif(index < 0):
				index += 1
			songs.insert(index, song)
		return songs


	def comparFun(self, song, title = True):
		if("pos" in song["options"]):
			return song["options"]["pos"]
		elif("num" in song["options"]):
			return song["options"]["num"] - self.indexing if song["options"]["num"] - self.indexing > 0 else 0
		elif(title is bool):
			return song["title"]
		else:
			return title


	def songsToString(self):
		songsStr = "\n\\setcounter{songnum}{" + str(self.indexing) + "}\n\\setcounter{page}{" + str(self.indexing) + "}\n"
		
		next_page = 0
		counter = self.indexing
		bool = False
		linesPerPage = 64 * 2
		
		for song in self.songLst:
			text = ""
			j = song["text"].find("]")
			
			before = song["options"]["pagebool"] if "pagebool" in song["options"] else True
			
			if("page" in song["options"]):
				next_page = linesPerPage * 1.5
				bool = True
			
			if("page" in song["options"] and before):
				text += self.handlePageConstraints(song)
				
			if("num" in song["options"].keys()):
				text += self.handleNumberConstraints(song, j, counter)
				
			else:
				next_page -= self.getNumOfLines(song["text"][j+1:])
				if(bool and next_page < 0):
					text += "\\pagenumbering{" + self.style + "}\n\\setcounter{page}{\\value{temppage} + 1}\n"
					bool = False
				text += self.handleNoConstraints(song, j, counter)
			
			if("page" in song["options"] and not before):
				text += self.handlePageConstraints(song)
				
			songsStr += "\n" + text + "\n"
			counter += 1
		return songsStr


	def handlePageConstraints(self, song):
		tempStyle = song["options"]["style"] if "style" in song["options"].keys() else "arabic"
		return "\\setcounter{temppage}{\\value{page}}\n\\pagenumbering{" + tempStyle + "}\n\\setcounter{page}{" + str(song["options"]["page"]) + "}\n"


	def handleNumberConstraints(self, song, j, counter):
		text = "\\setcounter{temp}{\\thesongnum}\n\\setcounter{songnum}{" + str(song["options"]["num"]) + "}"
		text += self.handleNoConstraints(song, j, counter)
		text += "\n\\setcounter{songnum}{\\thetemp + 1}"
		return text


	def handleNoConstraints(self, song, j, counter):
		return song["text"][:j+1] + "\\hypertarget{" + song["title"] + "}{}\n\\label{song" + str(counter) + "}\n" + song["text"][j+1:] + "\n"


	def getNumOfLines(self, song):
		num = 0
		song = re.sub("\\\w+", "a", song)
		for line in re.split("\n+", song):
			num += 1 + len(line) / 40
		return num


	def makeIndex(self):
		index_file = open("temp/titlefile.sbx",'w+', encoding = 'utf-8')
		
		for i in range(0, len(self.songLst)):
			index_file.write("\\idxentry{" + self.songLst[i]["title"] + "}{Sang nummer: \\hyperlink{" + self.songLst[i]["title"] + "}{" + str(self.indexing + i) + "} På side: \pageref{song" + str(self.indexing + i) + "}}\n")
		
		index_file.close()


	def fileRead(self, file):
		try:
			text = open(file, 'r', encoding = 'utf-8-sig').read()
		except:
			text = open(file, 'r').read()
		return text


	def addString(self, tag, string, tex):
		f = open("temp/SongBooklet.tex", 'w+', encoding = 'utf-8')
		tex = tex.replace(tag, string)
		f.write(tex)
		f.close()
		return tex
		

	def makeDirs(self):
		if not os.path.isdir("temp"):
			os.mkdir("temp")
		if not os.path.isdir("Booklet"):
			os.mkdir("Booklet")
		if not os.path.isdir("Songs"):
			os.mkdir("Songs")
		
	
def usage():
	print("Usage: " + sys.argv[0] + " -p <used to define new pagenumbering style> -s <choose pagenumbering style> -n <name of sangbook> -l <file for logo, svg or png>")
	print("Options: -c (if it is a camp) -u (if it is UNF) -e (if you do no want a front page) -S (if you want the songs to be sorted by title) -f (if you want the songs to be sorted by a fixed number)")


def main(argv):
	name = ""		   #name of the songbook
	style = ""		  #the chosen style
	logo = ""		   #the file containing the logo for the front page
	indexing = 0
	try:
		opts, args = getopt.getopt(argv, "hs:n:l:p:i:", ["help", "style=", "name=", "logo=", "number_style=", "indexing="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h","--help"):		  #option used to print usage
			usage()
			sys.exit()
		elif opt in ("-s", "--style"):	   #option used to set the pagenumber style in the tex file
			style = arg
		elif opt in ("-n", "--name"):		   #option used to set the name
			name = arg
		elif opt in ("-l", "--logo"):		   #option used to get a logo on the front page
			logo = arg
		elif opt in ("-i","--indexing"):		  #option used to print usage
			indexing = arg
		elif opt in ("-p", "--number_style"):		  #option used for making a new pagenumber style
			new_style = arg
			n = new_style.split(" ")[0]		#split the argument into two parts, a name
			s = new_style.split(" ")[1]		#and the style, that will be a regular expression
			if auxiliary.search_styles(n) != n:		 #check if the name is already in use, cannot have two styles by the same name
				style_tex.new_page_style(n, s)
				style = n
			else:
				print("There is already a style with that name.")
		else:
			usage()
			sys.exit()
			
	SongBooklet(name, style, logo, int(indexing)).makeBooklet()		 #call to create sangbog

if(__name__ == "__main__"):
	sys.exit(main(sys.argv[1:]))
