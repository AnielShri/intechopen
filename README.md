# intechopen.com webscraper
Downloads individual chapters from [intechopen](https://www.intechopen.com/) and merges it into a single ebook.

## Software dependencies
* `Python 3.6+` script interperter with typing support
* `PyPDF2` for merging chapters (tested with 1.26.0)
* `fpdf` for generating front page (tested with 1.7.2)

## Required directory structure
	intechopen/
		|----download_ebook.py
		|----pdfcache/
		|----ebooks/
	


## Usage
Simply edit the `url` variable in the `__main__` section to the base url of the desired ebook.

## Remarks
The quality of ebooks turned out to be quite dissapointing in the end. I was looking for literature about specific topics, but most books in intechopen are just journals. I don't expect to use this script much in the future, so updates/fixes may be lacking. 

## Note 
This script relies heavily on webscraping methods and will fail if the site layout of [intechopen](https://www.intechopen.com) ever changes
