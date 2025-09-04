from langchain_community.document_loaders import UnstructuredExcelLoader
excel_path = "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\structured_files\\inventory.xlsx"

loader = UnstructuredExcelLoader(file_path=excel_path)
docs= loader.load()
print(len(docs))
print(docs)