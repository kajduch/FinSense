import pymupdf
from ai.aiparser import Parser
from ai.aiassistant import Assistant

def parse_pdf(pdf_bytes, question):

    print('Файл получен')

    document = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    text = ""

    for page in document:
        text += page.get_text()

    aiparser = Parser()
    aiassistant = Assistant()

    result_json = aiparser.parse(text)
    result_advice = aiassistant.think(result_json)

    if not question:
        return (result_json, "")
    result_text = aiassistant.ask(result_json, question)

    return {
    "result_json": result_json,
    "advice_text": result_advice,
    "result_text": result_text
}