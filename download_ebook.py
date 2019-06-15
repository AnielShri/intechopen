
# ----------------------------------------------------------------------------#
# 
# Script to download complete ebooks from intechopen.com
# Was also a test case to play around with Python Typing
#
# Requirements:
# * Libraries:  - PyPDF2 => For merging chapters
# 				- fpdf => For generating front page
# 				- Other libraries are standard/common ...
# * Directories - ebooks => to store merged PDF
#				- pdfcache => to store individual chapters
#
# TODO:
# * Create pdfcache folder if not it does not already exsist
# * let user select ebook destination or use standard folder
# * check for commandline arguments
# * ask for user input 
#
#
# This script relies heavily on web scraping and will probably fail when
# intechopen changes something on the website/layout
#
# usage: just change "url" value in the __main__ part of this script
#
# ----------------------------------------------------------------------------#



# --- imports ----------------------------------------------------------------#

from typing import Optional, Any, Iterable, Tuple, List
import urllib.request, urllib.error, urllib.parse
import ssl
import re
import shutil
import sys, os
import PyPDF2, fpdf # seperate install

# --- classes ----------------------------------------------------------------#

class intechopen():
	def __init__(self, baseURL: str = None):
		self._baseURL = ""
		self._error: List = []
		self.baseURL = baseURL

	# --- class properties

	@property
	def lastError(self) -> List:
		return self._error

	@property
	def baseURL(self) -> Optional[str]:
		return self._baseURL

	@baseURL.setter
	def baseURL(self, baseURL: str = None) -> None:
		if not baseURL:
			return
		try:
			result = urllib.parse.urlparse(baseURL)
			if all([result.scheme, result.netloc, result.path]) == True:
				self._baseURL = baseURL
				print("New Base URL: {}".format(self._baseURL))
		except:
			# print("Base URL unchanged @ {}".format(self._baseURL))
			self._addError("Invalid URL: {}".format(baseURL))


	# --- private members

	def _addError(self, error: str) -> None:
		self._error.append(error)

	def _downloadString(self, url: str) -> Optional[str]:
		try:
			with urllib.request.urlopen(url) as response:
				html = response.read()
				return html.decode("utf-8")
		# on error
		except urllib.error.URLError as e:
			self._addError("URL Error occured: {}".format(e.reason))
		except urllib.error.HTTPError as e:
			self._addError("HTTP Error occured: {}".format(e.reason))
		except ValueError as e:
			self._addError("Unknown error")
			print(e)
		
		return None
	# end _downloadString


	def _downloadFile(self, url: str, dest: str) -> bool:
		try:
			sslcon = ssl.SSLContext() # fails otherwise
			with urllib.request.urlopen(url, context=sslcon) as response:
				with open(dest, "wb") as hfile:	
					shutil.copyfileobj(response, hfile)
					return True
			
		except urllib.error.URLError as e:
			self._addError("URLError in _downloadFile: {}".format(e.reason))
		except urllib.error.HTTPError as e:
			self._addError("HTTPError in _downloadFile: {}".format(e.reason))
		
		return False
	# end _downloadFile
	

	def _extractTitle(self, html: str) -> Optional[str]:
		title_expr = r'<h1 class="title" data-v-[\w\d]+>([^<]+)</h1>'
		subtitle_expr = r'<p class="subTitle" data-v-[\w\d]+>([^<]+)</p>'

		title_res = re.search(title_expr, html)

		if title_res is None:
			return None
		else:
			title = title_res.group(1)		
			subtitle_res = re.search(subtitle_expr, html)
			if subtitle_res is None:
				subtitle = ""
				str_title = "{}".format(title)
			else:
				subtitle = subtitle_res.group(1)
				str_title = "{} - {}".format(title, subtitle)			

			self._generateFront(title, subtitle)
			
			valid_title = re.sub('[^-a-zA-Z0-9.() ]', '_', str_title)
			return str_title
	# end _extractTitle


	# TODO: refactor
	def _generateFront(self, title: str, subtitle: str) -> bool:
		front_page = fpdf.FPDF(format="A5")
		front_page.add_page()
		front_page.set_draw_color(r=255, g=0, b=0)
		# front_page.set_text_color(r=255, g=255, b=255)
		# front_page.cell(w=210, h=297, txt="", fill=True)
		front_page.rect(x=10, y=10, w=128, h=190, style="D")
		front_page.set_margins(20, 20)
		# front_page.set_x(30)
		front_page.set_font("Times", "B", 24)
		front_page.ln(30)
		front_page.multi_cell(w=108, h=11, txt=title, align="C")
		# front_page.multi_cell(w=0, h=12, txt=self.baseURL, align="C")
		front_page.ln(20)
		front_page.set_font("Times", "", 16)
		front_page.multi_cell(w=108, h=7, txt=subtitle, align="C")
		# front_page.multi_cell(w=0, h=8, txt=self.baseURL, align="C")
		# front_page.ln(100)
		front_page.set_y(-40)
		front_page.set_font("Times", "", 11)
		# front_page.multi_cell(w=0, h=6, txt=self.baseURL, align="C", link=self.baseURL)
		front_page.write(h=5, txt=self.baseURL, link=self.baseURL)
		front_page.output(os.path.join(sys.path[0], "pdfcache", "front.pdf"))
		
		return True
	# end _generateFront

	
	def _extractChapters(self, html: str) -> Iterable:
		expr = r'<a href="([\w\d\-\/]+)" class="linkType1"'
		itfind = re.finditer(expr, html)
		return itfind
	# end _extractChapters


	def _extractPDFLink(self, html: str) -> Optional[Tuple[str, str]]:
		# expr = r'/chapter/pdf-download/([\d]+)'
		# expr = r'downloadPdfUrl:"([^"]+)'
		expr = r'citation-pdf-url/([\d]+)'
		result = re.search(expr, html)
		if result is not None: # download button
			link = "https://www.intechopen.com/chapter/pdf-download/{}".format(result.group(1))
			filename = "{}.pdf".format(result.group(1))
			return link, filename

		expr = r'https://cdn.intechopen.com/pdfs/([\d]+.pdf)'
		result = re.search(expr, html)
		if result is None:
			return None
		else:
			return result.group(0), result.group(1)		
	# end _extractPDFLink


	def _mergePDF(self, parts: List[str], dest: str) -> bool:
		pdf_merger = PyPDF2.PdfFileMerger()

		for path in parts:
			pdf_merger.append(path)

		with open(dest, "wb") as hfile:
			pdf_merger.write(hfile)

		pdf_merger.close() # explicit close

		return True
	# end _mergePDF


	def _clearCache(self, parts: List[str]) -> bool:
		try:
			for path in parts:
				os.remove(path)
			return True

		except Exception as e:
			self._addError("Error in _clearCache: {}".format(e))
		return False
	# end _clearCache


	# --- public members

	def DownloadBook(self, dest: str = None, url: str = None) -> bool:
		self.baseURL = url;
		if not self.baseURL:
			self._addError("Error in DownloadBook: Invalid Base URL given")
			return False

		base_html = self._downloadString(self._baseURL)
		if not base_html:
			self._addError("Error in DownloadBook: Empty BaseHTML")
			return False

		title = self._extractTitle(base_html)
		if not title:
			self._addError("Error in DownloadBook: unable to extract Title")
			return False

		# return False
				
		pdf_parts: List[str] = []
		pdf_parts.append(os.path.join(sys.path[0], "pdfcache", "front.pdf")) # TODO: refactor duplicated code

		links = self._extractChapters(base_html)
		for chapter in links:
			pdf_url = chapter.group(1)

			pdf_html = self._downloadString("https://www.intechopen.com{}".format(pdf_url))
			if not pdf_html:
				self._addError("Error in DownloadBook: Empty pdfHTML")
				return False
			
			pdf_data = self._extractPDFLink(pdf_html)
			if not pdf_data:
				self._addError("Error: Unable to extract PDF URL")
				return False

			# print("url: {}".format(pdfData[0]))
			pdf_file = os.path.join(sys.path[0], "pdfcache", pdf_data[1])
			pdf_parts.append(pdf_file)
			print("Filename: {}".format(pdf_data[1]))
			ret = self._downloadFile(pdf_data[0], pdf_file)
			if not ret:
				return False
		# end for

		# TODO: implement dest
		self._mergePDF(pdf_parts, "ebooks/{}.pdf".format(title))

		ret = self._clearCache(pdf_parts)
		if not ret:
			return False

			
		return True
	# end DownloadBook

# --- end intechopen ---------------------------------------------------------#





# -- main --------------------------------------------------------------------#

if __name__ == "__main__":
	print("# -----------------------------------------------------------------#")
	print("Download ebook from intechopen")

	# url = "https://www.intechopen.com/books/matlab-for-engineers-applications-in-control-electrical-engineering-it-and-robotics"
	# url = "https://www.intechopen.com/books/engineering-education-and-research-using-matlab"
	# url = "https://www.intechopen.com/books/fuzzy-logic-controls-concepts-theories-and-applications"
	# url = "https://www.intechopen.com/books/introduction-and-implementations-of-the-kalman-filter" # TODO: fails when text version is available => FIXED => added new regex @ _extractLink
	# url = "https://www.intechopen.com/books/technology-and-engineering-applications-of-simulink"
	url = "https://www.intechopen.com/books/applications-of-matlab-in-science-and-engineering" # TODO: fails @ _downloadFile
	# url = "https://www.intechopen.com/books/electric-power-conversion"
	# url = "https://www.intechopen.com/books/new-trends-in-electrical-vehicle-powertrains"
	# url = "https://www.intechopen.com/books/electric-machines-for-smart-grids-applications-design-simulation-and-control"
	# url = "https://www.intechopen.com/books/design-control-and-applications-of-mechatronic-systems-in-engineering"
	# url = "https://www.intechopen.com/books/electric-machines-for-smart-grids-applications-design-simulation-and-control"
	# url = "https://www.intechopen.com/books/pid-control-for-industrial-processes"
	# url = "https://www.intechopen.com/books/robust-control-theory-and-applications"
	# url = "https://www.intechopen.com/books/model-predictive-control" # TODO: fails at chapter 2 => FIXED
	# url = "https://www.intechopen.com/books/advances-in-pid-control" # TODO: fails at chapter 2 => FIXED => added new regex @ _extractLink => uses citation URL
	# url = "https://www.intechopen.com/books/technology-and-engineering-applications-of-simulink"
	# url = "https://www.intechopen.com/books/introduction-to-pid-controllers-theory-tuning-and-application-to-frontier-areas"
	# url = "https://www.intechopen.com/welcome/7c584de5f40193b636833aa812dab9d5"
	# url = "https://www.intechopen.com/books/design-control-and-applications-of-mechatronic-systems-in-engineering"




	ito = intechopen()
	print(ito.baseURL)
	ito.baseURL = url
	ito.DownloadBook()
	print(ito.baseURL)
	print(ito.lastError)
	print("Download complete!")
	