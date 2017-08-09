import os, sys, rstr
current_version = sys.version_info


def new_page_style(name, style):
	if isinstance(style, str):
		new_c = ""
		temp = style.replace("\\d", "10")		#replace the digit expression with 10, there is a total of 10 digits
		temp = temp.replace("[A-Z]", "26")		#replace the alphabet expression with 26, there is 26 letters in the alphabet
		temp = temp.replace("[a-z]", "26")		#replace the alphabet expression with 26, there is 26 letters in the alphabet
		temp = temp.replace("|", "+")			#replace the or symbol with +
		temp = temp.replace(")", ")*")			#replace the end paranthes with end paranthes and *
		temp = temp.replace("*+", "+")			#replace *+ with +
		temp = temp.replace("2610", "26*10")	#put a * in between the numbers
		temp = temp.replace("1026", "10*26")	#same
		temp = temp.replace("1010", "10*10")	#same
		temp = temp.replace("2626", "26*26")	#same
		total = eval(temp)	  #now we can evaluate it as a mathematical expression, total now contains the total amount of possible strings that can be generated by the regular expressions
		l = []
		while len(l) < total and len(l) < 65535:
			try:
				q = str(rstr.xeger(r"" + style + ""))	   #generate a string based on the regular expression
			except:
				print("regular expression in input is invalid")
				sys.exit(2)
			q = q.strip()		   #remove unnecessary '
			if q not in l:
				l.append(q)		 #add the string to the list of unique generated strings
		for i in range(0,len(l)):
			if i == 0:
				new_c += l[i]		   #add the element to string to be written
			elif i % 16 == 0:
				new_c += "\n\\or " + l[i]	   #add the element, a newline and a \or, to string to be written
			else:
				new_c += "\\or " + l[i]		 #add the element and a \or, to string to be written
		else:
			print("invalid input")

	f = open("Resources/page_numbering.tex", 'r')
	s = f.read()
	f.close()
	s = s.replace("\\makeatother", "")		   #remove the \makeatother
	s += "\\newcommand*{\\" + name + "}[1]{%\n\\expandafter\\@" + name + "\\csname c@#1\\endcsname\n}\n\n\\newcommand*{\\@" + name + "}[1]{%\n$\\ifcase#1\n"	 #create the command for the new style
	s += new_c
	s += "\n" + "\n\\else\\@ctrerr\\fi$\n}\n\\makeatother"	 #add the end of the command plus \makeatother
	f = open("Resources/page_numbering.tex", 'w')
	f.write(s)
	f.close()

def main(arg1):
	new_page_style(arg1[0], arg1[1:])

if __name__=='__main__':
	sys.exit(main(sys.argv[1:]))
