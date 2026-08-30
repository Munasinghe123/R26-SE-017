from pypdf import PdfReader


def read_document(path):

    if path.endswith(".txt"):

        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    elif path.endswith(".pdf"):

        reader = PdfReader(path)

        text = ""

        for page in reader.pages:
            text += page.extract_text() + "\n"

        return text

    else:
        raise Exception("Unsupported document type")