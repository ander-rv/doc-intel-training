import os
from pprint import pprint

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from dotenv import load_dotenv


# cargar el archivo .env a las variables de entorno
load_dotenv()

# cargar variables de entorno
DOC_INTEL_ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT", "")
DOC_INTEL_API_KEY = os.getenv("DOC_INTEL_API_KEY", "")
TEST_FILE_PATH = os.getenv("TEST_FILE_PATH", "")
DOC_INTEL_MODEL_PREBUILT_LAYOUT = os.getenv("DOC_INTEL_MODEL_PREBUILT_LAYOUT", "")


def analize_doc(file_path: str, model: str):
    """
    Analiza un documento utilizando Azure Document Intelligence.

    Esta función envía un archivo a Azure Document Intelligence para que sea
    procesado con el modelo especificado y devuelve el resultado del análisis
    una vez finalizada la operación.

    Args:
        file_path (str): Ruta al archivo que se desea analizar.
        model (str): Identificador del modelo que se utilizará para el análisis
            (por ejemplo: "prebuilt-layout", "prebuilt-read" o un modelo personalizado).

    Returns:
        AnalyzeResult: Objeto con el resultado del análisis del documento,
        que incluye información estructurada como texto, tablas, layout
        y otros elementos detectados.

    Raises:
        FileNotFoundError: Si el archivo indicado en la ruta no existe.
        AzureError: Si ocurre un error durante la llamada al servicio de Azure.
    """
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=DOC_INTEL_ENDPOINT, credential=AzureKeyCredential(DOC_INTEL_API_KEY)
    )

    poller = document_intelligence_client.begin_analyze_document(
        model_id=model, body=open(file_path, "rb")
    )

    return poller.result()


def tables_to_dict(result: AnalyzeResult) -> dict[str, str]:
    """
    Convierte las tablas detectadas en el resultado de Azure Document Intelligence
    en un diccionario de pares clave-valor.

    La función recorre todas las tablas presentes en el objeto `AnalyzeResult`,
    reconstruye su contenido en una estructura de filas y columnas, y asume que
    cada fila representa un par clave-valor donde la primera columna es la clave
    y la segunda columna es el valor.

    Args:
        result (AnalyzeResult): Resultado del análisis de un documento generado
            por Azure Document Intelligence.

    Returns:
        dict[str, str]: Diccionario donde las claves corresponden a los códigos
        o campos detectados en la primera columna de las tablas y los valores
        a su contenido asociado en la segunda columna.

    Notes:
        Esta función está pensada para documentos estructurados como fichas
        técnicas o formularios donde los datos aparecen en formato campo-valor
        dentro de tablas.
    """
    data: dict[str, str] = {}

    for table in result.tables: # type: ignore
        grid = [["" for _ in range(table.column_count)] for _ in range(table.row_count)]

        for cell in table.cells:
            grid[cell.row_index][cell.column_index] = cell.content.strip()

        for row in grid:
            if len(row) >= 2:
                key = row[0]
                value = row[1]
                if key:
                    data[key] = value

    return data


def main():
    result = analize_doc(file_path=TEST_FILE_PATH, model=DOC_INTEL_MODEL_PREBUILT_LAYOUT)
    data = tables_to_dict(result)
    pprint(data)

    print(f'\nLa marca del coche es "{data["D.1"]}"')


if __name__ == "__main__":
    main()
