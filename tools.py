from typing import Optional
import os
from crewai_tools import tool, BaseTool
from pypdf import PdfReader
import functools
import shelve
import constants

@tool("AddToScreeningMemo")
def add_to_screening_memo(section: str, data: str) -> str:
    """
    This tool is how you will fill out your screening memo. This fills in one section of the memo at a time.
    Below are the following valid sections:
        sections = [
        "<[Firm Overview]>",
        "<[Fundraise Summary & Timing]>",
        "<[Diligence Items]>",
        "<[Conclusions]>",
        "<[Overview]>",
        "<[Market Opportunity]>",
        "<[Differentiation & Winning Deals]>",
        "<[Sourcing & Picking Deals]>",
        "<[Post-Investment]>",
        "<[Exiting Deals]>",
        "<[Fund Team]>",
        "<[Co-Investment Views]>",
    ]

    """
    if section not in constants.SECTIONS:
        raise ValueError(f"The section you entered `{section}` is not valid. It must be one of the following:\n{constants.SECTIONS}")

    if not os.path.exists("./outputs/shelve-db"):
        os.mkdir("./outputs/shelve-db")
    with shelve.open("./outputs/shelve-db/db") as db:
        if db.get(section) is None:
            db[section] = data
            return "Operation successful!"
        db[section] = db[section] + "<[SEP]>" + data
    return "Operation successful!"
    
@tool("ReadScreeningMemo")
def read_screening_memo(section: Optional[str] = None) -> str:
    """
    This tools allows you to read the current data in a screening memo.
    You can specify a section to see only the text in that section. 
    Below are the following valid sections:
        sections = [
        "<[Firm Overview]>",
        "<[Fundraise Summary & Timing]>",
        "<[Diligence Items]>",
        "<[Conclusions]>",
        "<[Overview]>",
        "<[Market Opportunity]>",
        "<[Differentiation & Winning Deals]>",
        "<[Sourcing & Picking Deals]>",
        "<[Post-Investment]>",
        "<[Exiting Deals]>",
        "<[Fund Team]>",
        "<[Co-Investment Views]>",
    ]
    If you leave the section argument blank, this will return the data for all sections.
    """

    if section is None:
        with shelve.open("./outputs/shelve-db/db") as db:
            return str(dict(db))
    if section not in constants.SECTIONS:
        return ValueError(f"Argument `section` must be one of the following: {constants.SECTIONS}")
    with shelve.open("./outputs/shelve-db") as db:
        return str(db.get(section))

def gen_qd(dataroom_path):
    class QueryDataroom(BaseTool):
        name: str = "QueryDataroom"
        description: str =     """
        Takes a filename of a file in the data room as an argument. 
        This tool will read and then return the context of that file as text.
        """

        def _run(self, filename: str) -> str:
            if cache(filename):
                return "You've already read this file."
            
            full_filename = os.path.join(dataroom_path, filename)
            if not os.path.exists(full_filename):
                files = os.listdir(dataroom_path)
                return f"`{filename}` does not exist in the dataroom\n \
                    Files in dataroom: {files}"
            
            if full_filename.endswith('.pdf'):
                return self.read_pdf(full_filename)
            
            with open(full_filename, 'r') as f:
                return f.read()
            
        @staticmethod
        @functools.cache
        def read_pdf(filepath: str) -> str:
            reader = PdfReader(filepath)
            text = '\n\n'.join(page.extract_text() for page in reader.pages)
            return text
    return QueryDataroom

def cache(arg, a=[]):
    if arg not in a:
        a.append(arg)
        return False
    return True