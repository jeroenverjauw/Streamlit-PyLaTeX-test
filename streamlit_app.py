import base64
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import run, PIPE
# from zipfile import ZipFile

import streamlit as st
# from streamlit_ace import st_ace

from utils import latex


class PdfLatexException(Exception):
    """Exception raised for errors in the pdflatex execution.

    Attributes:
        stderr -- stderr which caused the error
        message -- explanation of the error
    """

    def __init__(self, stderr, message="PdfLaTeX did not run successfully"):
        self.salary = stderr
        self.message = message
        super().__init__(self.message)


# set basic page config
st.set_page_config(page_title="LaTeX to PDF Converter",
                    page_icon='📄',
                    layout='wide',
                    initial_sidebar_state='expanded')

# apply custom css if needed
# with open('utils/style.css') as css:
#     st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)


def get_pdflatex_path() -> str:
    '''Get path of pdflatex executable
    returns: path of pdflatex executable
    '''
    pdflatex_path = shutil.which("pdflatex")
    return pdflatex_path


@st.cache_resource(ttl=60*60*24)
def cleanup_tempdir() -> None:
    '''Cleanup temp dir for all user sessions.
    Filters the temp dir for uuid4 subdirs.
    Deletes them if they exist and are older than 1 day.
    '''
    deleteTime = datetime.now() - timedelta(days=1)
    # compile regex for uuid4
    uuid4_regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    uuid4_regex = re.compile(uuid4_regex)
    tempfiledir = Path(tempfile.gettempdir())
    if tempfiledir.exists():
        subdirs = [x for x in tempfiledir.iterdir() if x.is_dir()]
        subdirs_match = [x for x in subdirs if uuid4_regex.match(x.name)]
        for subdir in subdirs_match:
            itemTime = datetime.fromtimestamp(subdir.stat().st_mtime)
            if itemTime < deleteTime:
                shutil.rmtree(subdir)


@st.cache_data(show_spinner=False)
def make_tempdir() -> Path:
    '''Make temp dir for each user session and return path to it
    returns: Path to temp dir
    '''
    if 'tempfiledir' not in st.session_state:
        tempfiledir = Path(tempfile.gettempdir())
        tempfiledir = tempfiledir.joinpath(f"{uuid.uuid4()}")   # make unique subdir
        tempfiledir.mkdir(parents=True, exist_ok=True)  # make dir if not exists
        st.session_state['tempfiledir'] = tempfiledir
    return st.session_state['tempfiledir']


def store_file_in_tempdir(tmpdirname: Path, filename:str, tex: str) -> Path:
    '''Store file in temp dir and return path to it
    params: tmpdirname: Path to temp dir
            filename: str
            tex: str
    returns: Path to stored file
    '''
    # store file in temp dir
    tmpfile = tmpdirname.joinpath(filename)
    with open(tmpfile, 'w') as f:
        f.write(tex)
    return tmpfile


@st.cache_data(show_spinner=False)
def get_base64_encoded_bytes(file_bytes) -> str:
    base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
    return base64_encoded


@st.cache_data(show_spinner=False)
def show_pdf_base64(base64_pdf):
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1200px" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_versions() -> str:
    try:
        result = run(["pdflatex", "--version"], capture_output=True, text=True)
        lines = result.stdout.strip()
        pdflatex_version = lines.splitlines()[0]
    except FileNotFoundError:
        pdflatex_version = 'pdflatex NOT found...'
    versions = f'''
    - `Streamlit {st.__version__}`
    - `{pdflatex_version}`
    '''
    return versions


def get_all_files_in_tempdir(tempfiledir: Path) -> list:
    files = [x for x in tempfiledir.iterdir() if x.is_file()]
    files = sorted(files, key=lambda f: f.stat().st_mtime)
    return files


def delete_all_files_in_tempdir(tempfiledir: Path):
    for file in get_all_files_in_tempdir(tempfiledir):
        file.unlink()


def delete_files_from_tempdir_with_same_stem(tempfiledir: Path, file_path: Path):
    file_stem = file_path.stem
    for file in get_all_files_in_tempdir(tempfiledir):
        if file.stem == file_stem:
            file.unlink()


def get_bytes_from_file(file_path: Path) -> bytes:
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    return file_bytes


@st.cache_data(show_spinner=False)
def get_base64_encoded_bytes(file_bytes) -> str:
    base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
    return base64_encoded


@st.cache_data(show_spinner=False)
def show_pdf_base64(base64_pdf):
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000px" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def check_if_file_with_same_name_and_hash_exists(tempfiledir: Path, file_name: str, hashval: int) -> bool:
    """Check if file with same name and hash already exists in tempdir
    params: tempfiledir: Path to file
            file_name: name of file
            hashval: hash of file
    returns: True if file with same name and hash already exists in tempdir
    """
    file_path = tempfiledir.joinpath(file_name)
    if file_path.exists():
        file_hash = hash((file_path.name, file_path.stat().st_size))
        if file_hash == hashval:
            return True
    return False


def show_sidebar():
    with st.sidebar:
        st.image('resources/latex.png', width=260)
        st.header('About')
        st.markdown('''This app can convert **LaTeX** Documents to PDF.
                    Not all LaTeX files can be converted successfully.
                    References to other files are not supported.
                    Maybe some latex packages are missing.''')
        st.markdown('''Supported input file formats are:''')
        st.markdown('''- `tex`''')
        st.markdown('''---''')
        st.subheader('Versions')
        st.markdown(get_versions(), unsafe_allow_html=True)
        st.markdown('''---''')
        st.subheader('GitHub')
        st.markdown('''<https://github.com/Franky1/Streamlit-PyLaTeX>''')


def new_file_uploaded():
    if st.session_state.get('upload') is not None:
        st.session_state['texdata'] = st.session_state['upload'].read().decode('utf-8')
        st.session_state['filename'] = st.session_state['upload'].name
        store_file_in_tempdir(st.session_state['tempfiledir'], st.session_state['filename'], st.session_state['texdata'])


def convert_tex_to_pdf_native(tex_file: str, output_dir: Path=Path("."), timeout: int=60):
    """Converts a tex file to pdf using pdflatex.
    Calls pdflatex directly.
    params: tex_file: str name to tex file
            output_dir: Path to output dir
            timeout: timeout for subprocess in seconds
    returns: (output, exception)
            output: Path to converted file
            exception: Exception if conversion failed
    """
    filepath = None
    exception = None
    stdout = None
    try:
        process = run(args=['pdflatex', '-interaction=nonstopmode', '-output-format=pdf', f'-output-directory={output_dir.resolve()}', tex_file],
            stdout=PIPE, stderr=PIPE, cwd=output_dir,
            timeout=timeout, text=True)
        stdout = process.stdout
        re_filename = re.search('Output written on (.*?pdf) ', stdout)
        re_fatal = re.search('.* (Fatal error occurred, no output PDF file produced)', stdout)
        if re_filename is not None:
            filepath = Path(re_filename[1]).resolve()
        elif re_fatal is not None:
            raise PdfLatexException(re_fatal[1])
        else:
            raise PdfLatexException('Unknown error')
    except Exception as e:
        exception = e
    return (filepath, exception, stdout)


if __name__ == "__main__":
    if st.session_state.get('texdata') is None:
        st.session_state['texdata'] = ''
    cleanup_tempdir()  # cleanup temp dir from previous user sessions
    tmpdirname = make_tempdir()  # make temp dir for each user session
    if st.session_state.get('tempfiledir') is None:
        st.session_state['tempfiledir'] = tmpdirname
    show_sidebar()
    st.title('LaTeX to PDF Converter 📄')
    hcol1, hcol2 = st.columns([1,1], gap='large')
    with hcol1:
        st.file_uploader('Upload your own LaTeX file', type=['tex'], on_change=new_file_uploaded, key='upload')
    with hcol2:
        if st.button('Generate example LaTex file with pylatex', key='example'):
            document = latex.make_doc()
            st.session_state['texdata'] = latex.get_tex(document)
            st.session_state['filename'] = 'example.tex'
            store_file_in_tempdir(st.session_state['tempfiledir'], st.session_state['filename'], st.session_state['texdata'])
        if st.button('Load "sample1.tex" LaTex file', key='sample1'):
            st.session_state['texdata'] = get_bytes_from_file(Path('samples').joinpath('sample1.tex')).decode('utf-8')
            st.session_state['filename'] = 'sample1.tex'
            store_file_in_tempdir(st.session_state['tempfiledir'], st.session_state['filename'], st.session_state['texdata'])
        if st.button('Load "sample2.tex" LaTex file', key='sample2'):
            st.session_state['texdata'] = get_bytes_from_file(Path('samples').joinpath('sample2.tex')).decode('utf-8')
            st.session_state['filename'] = 'sample2.tex'
            store_file_in_tempdir(st.session_state['tempfiledir'], st.session_state['filename'], st.session_state['texdata'])
    st.markdown('''---''')
    col1, col2 = st.columns([1,1], gap='large')
    with col1:
        if st.session_state.get('filename'):
            st.subheader(f'''Preview the LaTeX file "{st.session_state.get('filename')}"''')
        else:
            st.subheader('Preview the LaTeX file')
        if st.session_state.get('texdata'):
            st.code(body=st.session_state.get('texdata'), language='latex')
            # FIXME: Ace Editor does not work, cannot be updated
            # st.session_state['content'] = st.text_area('LaTeX file', value=st.session_state.get('rawdata'), height=800, key='text_area')
            # st.session_state['content'] = st_ace(value=st.session_state.get('texdata'), height=800, language='latex', theme='monokai', key='ace', auto_update=True)
    with col2:
        st.subheader('Preview the generated PDF file')
        if st.button('Generate PDF file from LaTeX'):
            if st.session_state.get('texdata') is not None:
                filepath, exception, stdout = convert_tex_to_pdf_native(st.session_state['filename'], st.session_state['tempfiledir'])
                if exception is None:
                    if filepath is not None:
                        st.session_state['pdffilepath'] = filepath
                        st.session_state['pdfbytes'] = get_bytes_from_file(st.session_state.pdffilepath)
                        st.session_state['pdfbase64'] = get_base64_encoded_bytes(st.session_state.pdfbytes)
                        st.session_state['pdfhash'] = hash((filepath.name, filepath.stat().st_size))
                        st.success(f'PDF file generated successfully: {st.session_state.pdffilepath.name}')
                        show_pdf_base64(st.session_state.pdfbase64)
                        st.download_button(label='Download PDF file',
                            data=st.session_state.pdfbytes,
                            file_name=st.session_state.pdffilepath.name,
                            mime='application/octet-stream',
                            key='download_button')
                    else:
                        st.error('PDF file not generated')
                else:
                    st.error(f'{exception}; Error log see below')
                    st.code(body=stdout, language='log')
