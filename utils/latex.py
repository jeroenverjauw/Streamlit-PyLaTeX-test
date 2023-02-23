'''
This is a simple example of how to use pylatex to generate a pdf file.
It was taken from the pylatex documentation:
https://jeltef.github.io/PyLaTeX/current/examples/basic.html
'''
from pathlib import Path

from pylatex import Command, Document, Section, Subsection
from pylatex.utils import NoEscape, italic


def fill_document(doc):
    """Add a section, a subsection and some text to the document.

    :param doc: the document
    :type doc: :class:`pylatex.document.Document` instance
    """
    with doc.create(Section('A section')):
        doc.append('Some regular text and some ')
        doc.append(italic('italic text. '))

        with doc.create(Subsection('A subsection')):
            doc.append('Also some crazy characters: $&#{}')


def make_doc() -> Document:
    # Document with `\maketitle` command activated
    doc = Document()

    doc.preamble.append(Command('title', 'Awesome Title'))
    doc.preamble.append(Command('author', 'Anonymous author'))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))

    fill_document(doc)

    # Add stuff to the document
    with doc.create(Section('A second section')):
        doc.append('Some text.')

    return doc


def get_tex(doc: Document) -> str:
    return doc.dumps()


def generate_tex_file(doc: Document, filepath: str) -> None:
    doc.generate_tex(filepath)


def generate_pdf_file(doc: Document, filepath: str) -> None:
    doc.generate_pdf(filepath, compiler='pdflatex', silent=False)


def make_doc_from_tex(default_filepath:str, tex: str) -> Document:
    doc = Document(default_filepath=default_filepath, data=NoEscape(tex))
    # doc.append(NoEscape(tex))
    return doc


if __name__ == "__main__":
    '''
    This is only to test the functions in this module.
    '''
    doc = make_doc()
    tex = get_tex(doc)
    print(tex)
    generate_tex_file(doc, Path('demo').name)
    # generate_pdf(doc)
