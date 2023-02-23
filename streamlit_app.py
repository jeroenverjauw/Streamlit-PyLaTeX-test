import base64
import re
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from subprocess import run
from zipfile import ZipFile

import streamlit as st
from streamlit_ace import st_ace

from utils import latex

sys.path.insert(0,'/usr/bin')

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


def store_file_in_tempdir(tmpdirname: Path, uploaded_file: BytesIO) -> Path:
    '''Store file in temp dir and return path to it
    params: tmpdirname: Path to temp dir
            uploaded_file: BytesIO object
    returns: Path to stored file
    '''
    # store file in temp dir
    tmpfile = tmpdirname.joinpath(uploaded_file.name)
    with open(tmpfile, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return tmpfile


@st.cache_data(show_spinner=False)
def get_base64_encoded_bytes(file_bytes) -> str:
    base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
    return base64_encoded


@st.cache_data(show_spinner=False)
def show_pdf_base64(base64_pdf):
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000px" type="application/pdf"></iframe>'
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
        st.markdown('''This app can convert **LaTeX** Documents to PDF.''')
        st.markdown('''Supported input file formats are:''')
        st.markdown('''- `tex`''')
        st.markdown('''---''')
        st.subheader('Versions')
        st.markdown(get_versions(), unsafe_allow_html=True)
        # st.info(get_pdflatex_path())
        st.markdown('''---''')
        st.subheader('GitHub')
        st.markdown('''<https://github.com/Franky1/Streamlit-PyLaTeX>''')


def new_file_uploaded():
    if st.session_state.get('upload') is not None:
        st.session_state['rawdata'] = st.session_state['upload'].read().decode('utf-8')


if __name__ == "__main__":
    if st.session_state.get('rawdata') is None:
        st.session_state['rawdata'] = ''
    if st.session_state.get('content') is None:
        st.session_state['content'] = ''
    cleanup_tempdir()  # cleanup temp dir from previous user sessions
    tmpdirname = make_tempdir()  # make temp dir for each user session
    show_sidebar()
    st.title('LaTeX to PDF Converter 📄')
    hcol1, hcol2 = st.columns([1,1], gap='large')
    with hcol1:
        st.file_uploader('Upload your LaTeX file', type=['tex'], on_change=new_file_uploaded, key='upload')
    with hcol2:
        if st.button('Generate example LaTex file', key='example'):
            document = latex.make_doc()
            st.session_state['rawdata'] = latex.get_tex(document)
        if st.button('Load sample1 LaTex file', key='sample1'):
            st.session_state['rawdata'] = get_bytes_from_file(Path('samples').joinpath('sample1.tex')).decode('utf-8')
        if st.button('Load sample2 LaTex file', key='sample2'):
            st.session_state['rawdata'] = get_bytes_from_file(Path('samples').joinpath('sample2.tex')).decode('utf-8')
    st.markdown('''---''')
    col1, col2 = st.columns([3,2], gap='medium')
    with col1:
        st.subheader('Preview the LaTeX file')
        # FIXME: Ace Editor cannot be updated
        # st.session_state['content'] = st.text_area('LaTeX file', value=st.session_state.get('rawdata'), height=800, key='text_area')
        # st.session_state['content'] = st_ace(value=st.session_state.get('rawdata'), height=800, language='latex', theme='monokai', key='ace', auto_update=True)
        st.code(body=st.session_state.get('rawdata'), language='latex')
        st.session_state['content'] = st.session_state.get('rawdata')
    with col2:
        st.subheader('Preview the generated PDF file')
        if st.button('Generate PDF file from LaTeX'):
            # st.info(len(st.session_state['rawdata']))
            if st.session_state.get('content') is not None:
                document = latex.make_doc_from_tex(default_filepath=tmpdirname.name, tex=st.session_state.get('content'))
                # st.info(len(document.dumps()))
                latex.generate_pdf_file(doc=document, filepath='output')



        # # get uploaded file
        # uploaded_file = st.file_uploader('Upload your LaTeX file', type=['tex'])
        # if uploaded_file is not None:
        #     # store file in temp dir
        #     tmpfile = store_file_in_tempdir(tmpdirname, uploaded_file)
        #     # delete all files with same stem
        #     delete_files_from_tempdir_with_same_stem(tmpdirname, tmpfile)
        #     # check if file with same name and hash already exists in tempdir
        #     if check_if_file_with_same_name_and_hash_exists(tmpdirname, tmpfile.name, hash(tmpfile)):
        #         st.warning('File with same name and hash already exists in tempdir')
        #     else:
        #         # convert file to pdf
        #         convert_tex_to_pdf(tmpfile)
        #         # get pdf file
        #         pdf_file = Path(tmpfile.stem + '.pdf')
        #         # show pdf
        #         if pdf_file.exists():
        #             file_bytes = get_bytes_from_file(pdf_file)
        #             base64_pdf = get_base64_encoded_bytes(file_bytes)
        #             show_pdf_base64(base64_pdf)
        #         else:
        #             st.error('PDF file does not exist')
        # else:
        #     st.warning('Please upload a LaTeX file')
