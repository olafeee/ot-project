import os, subprocess
from os import walk
import os.path

import xlsxwriter

def getLibraries(binary):
	proc = subprocess.Popen(['readelf','-d',binary], stdout=subprocess.PIPE)
	tmp = proc.stdout.read()

	tmp=tmp.split("\n")

	libs = []

	for line in tmp:
	    if "(NEEDED)" in line:
	        line = line.split("[")
	        line = line[1]
	        line = line.split("]")
	        line = line[0]
	        libs.append(line)
	        # libs+=line

	return libs

def locateLibary(lib):
	proc = subprocess.Popen(['locate',lib], stdout=subprocess.PIPE)
	tmp = proc.stdout.read()
	return tmp


def getPIE(file, type):
	# print "test"
	proc = subprocess.Popen(['bash','checksec.sh','--file',file], stdout=subprocess.PIPE)
	tmp = proc.stdout.read()

	# RELRO, SC, NX, PIE
	rstring=[file, "n",0,0,"nopiee","pielib"]

	if "Error: Not an ELF" in tmp:
		return "error"
	else:
		if "No PIE" in tmp:
			rstring[4] = "nopie"
		if not "No PIE" in tmp:
			if type is "lib":
				if "DSO" in tmp: 
					rstring[4] = "pie"
			elif type is "bin":
				if "PIE enabled" in tmp: 
					rstring[4] = "pie"

		if "No RELRO" in tmp:
			rstring[1] = "n"
		elif "Partial RELRO" in tmp:
			rstring[1] = "p"
		elif "Full RELRO" in tmp:
			rstring[1] = "f"
		
		#stack canary
		if "No canary found" in tmp:
			rstring[2] = 0
		elif "Canary found" in tmp:
			rstring[2] = 1

		#stack canary
		if "NX disabled" in tmp:
			rstring[3] = 0
		elif "NX enabled" in tmp:
			rstring[3] = 1
		return rstring

def check(binary):
	result = [binary,"x","y"]
	libs = getLibraries(binary)
	yarr=[]
	for lib in libs:
		libresult = locateLibary(lib)
		libresult=libresult.split("\n")
		for p in libresult:
			if not p: p = "empty"
			y = getPIE(p,'lib')
			if y[4] == "nopie": result[2]="nopie"
			yarr.append(y)
			# print y

	x = getPIE(binary, "bin")
	# if x == "error":
	# 	return 0
	# else:
	result[1] = x[4]
	if result[2] == "y": result[2] = "pie"

	try:
		x[5] = result[2]
	except Exception, e:
		pass

	

	returna=[result, x, yarr]
	return returna

def checkAllBins():
	fresult = []
	pie=0
	nopie=0
	err=0
	binArray=[]
	libArray=[]
	bindirs = [	"/usr/bin/",
				"/usr/sbin/",
				"/bin/",
				"/sbin/"]

	for dirs in bindirs:
		f = []
		for (dirpath, dirnames, filenames) in walk(dirs):
			f.extend(filenames)
			break
		
		for file in f:		
			binary = dirs+file
			result = check(binary)
			if result[0]:
				fresult.append(result[0])
			if result[1] is not "error": binArray.append(result[1])
			for y in result[2]:
				if y is not "error":
					if y[0] is not "empty":
						libArray.append(y)
						print y

	for r in fresult:
		if r[1] == "pie" and r[2] == "pie":
			pie+=1
		else:
			if r[1] == "error" or r[2] == "error":
				err+=1
			else:
				nopie+=1

	print "pie  :",pie
	print "nopie:",nopie
	print "err  :",err

	# Create a workbook and add a worksheet.
	workbook = xlsxwriter.Workbook('bin.xlsx')
	worksheet = workbook.add_worksheet()
	# Start from the first cell. Rows and columns are zero indexed.
	row = 0
	col = 0

	# Iterate over the data and write it out row by row.
	for file, relro, sc, nx, pie, pielib in (binArray):
		worksheet.write(row, col,     file)
		worksheet.write(row, col + 1, relro)
		worksheet.write(row, col + 2, sc)
		worksheet.write(row, col + 3, nx)
		worksheet.write(row, col + 4, pie)
		worksheet.write(row, col + 5, pielib)		
		row += 1

	workbook.close()
	workbook = xlsxwriter.Workbook('lib.xlsx')
	worksheet = workbook.add_worksheet()
	# Start from the first cell. Rows and columns are zero indexed.
	row = 0
	col = 0

	# Iterate over the data and write it out row by row.
	for file, relro, sc, nx, pie, pielib in (libArray):
		worksheet.write(row, col,     file)
		worksheet.write(row, col + 1, relro)
		worksheet.write(row, col + 2, sc)
		worksheet.write(row, col + 3, nx)
		worksheet.write(row, col + 4, pie)		
		row += 1

	workbook.close()

# proc = subprocess.Popen(['bash','checksec.sh',], stdout=subprocess.PIPE)
# tmp = proc.stdout.read()

# if tmp is not "No such file or directory":
	# checkAllBins()

x = os.path.isfile("checksec.sh")

if not x:
	subprocess.call(["wget", "http://www.trapkit.de/tools/checksec.sh"])

x = os.path.isfile("checksec.sh")

if x:
	checkAllBins()
elif not x:
	print "checksec.sh download failed, download the file manualyyasdasd"

# getPIE(binary, "bin")

# getBinaries()