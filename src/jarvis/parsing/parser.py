'''
    A simple parser that will help us parse both PDFs,txt and docx files.
    It will return a list of chunks of text that can be embedded using OpenAI embeddings(embedded.py).
'''

import io
from dataclasses import dataclass

from docx import Document
from pypdf import PdfReader
from jarvis.settings import settings
from jarvis.logger import setup_logger

logger=setup_logger('parser')

ALLOWED_FILE_TYPES = settings.ALLOWED_FILE_TYPES
CHUNK_SIZE = settings.CHUNK_SIZE
CHUNK_OVERLAP = settings.CHUNK_OVERLAP


@dataclass
class Chunk:
    text: str
    slice_start: int  # char offsets into the source text; per page when page_no is set
    slice_end: int
    page_no: int | None = None  # 1-based, pdf only: python-docx cannot tell page breaks


def chunk_overlap(text:str, chunk_size:int=CHUNK_SIZE, chunk_overlap:int=CHUNK_OVERLAP, page_no:int|None=None)->list[Chunk]:
    '''
    Splits the text into chunks of a specified size, with a specified overlap.
    Upgrade to this function to use a more advanced chunking algorithm that will split the text into chunks based on sentences and paragraphs.
    '''
    if chunk_size<=0:
        logger.error("Chunk size must be greater than 0")
        raise ValueError("Chunk size must be greater than 0")
    if chunk_overlap<0:
        logger.error("Chunk overlap must be greater than or equal to 0")
        raise ValueError("Chunk overlap must be greater than or equal to 0")
    if chunk_overlap>=chunk_size:
        logger.error("Chunk overlap must be less than chunk size")
        raise ValueError("Chunk overlap must be less than chunk size")
    chunks = []
    start=0
    
    while start<len(text):
        end= min(start+chunk_size,len(text))
        chunks.append(Chunk(text[start:end], start, end, page_no))
        
        if end==len(text):
            break
        
        start = end - chunk_overlap

    return chunks


class Parser():
    
    def parse(self,file_name:str,file_bytes:bytes)->list[Chunk]:
        '''
            This function will parse the file and return a list of chunks of text.
            It will check the file type and call the appropriate parser.
        '''
        file_name=file_name.lower()
        file_type = file_name.split('.')[-1]
        if file_type not in ALLOWED_FILE_TYPES:
            raise ValueError(f"File type {file_type} is not allowed. Allowed file types are {ALLOWED_FILE_TYPES}")
        
        if file_type == 'pdf':
            return self.parse_pdf(file_bytes)
        elif file_type in ('txt', 'md'):
            return self.parse_txt(file_bytes)
        elif file_type == 'docx':
            return self.parse_docx(file_bytes)
        
    def parse_pdf(self,file_bytes:bytes)->list:
        '''
            This function will parse the pdf file and return a list of chunks of text.
            It will use the pypdf library to read the pdf file.
        '''
        reader = PdfReader(io.BytesIO(file_bytes))
        # chunks never cross a page, so every chunk has one page_no
        return [c for i, page in enumerate(reader.pages, 1)
                for c in chunk_overlap(page.extract_text() or "", page_no=i)]

    def parse_txt(self,file_bytes:bytes)->list:
        '''
            This function will parse the txt file and return a list of chunks of text.
        '''
        return chunk_overlap(file_bytes.decode("utf-8"))

    def parse_docx(self,file_bytes:bytes)->list:
        '''
            This function will parse the docx file and return a list of chunks of text.
            It will use the python-docx library to read the docx file.
        '''
        doc = Document(io.BytesIO(file_bytes))
        return chunk_overlap("\n".join(p.text for p in doc.paragraphs))

    

parser = Parser()