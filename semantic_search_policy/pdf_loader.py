"""
使用PyMuPDF读取docs_pdf中的PDF文件，提取纯文本，保存到txt文件备用。
"""
import fitz  # PyMuPDF
import os


def split_text(text, chunk_size=500, overlap=50):
    """将文本按固定大小切片，带适量重叠，以便向量化检索。"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # 重叠部分
    return chunks


def extract_pdfs(pdf_folder, output_folder):
    os.makedirs(pdf_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)
            txt_name = filename.replace(".pdf", ".txt")
            txt_path = os.path.join(output_folder, txt_name)
            with fitz.open(pdf_path) as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"提取完成：{filename} -> {txt_name}，共{len(text)}字符")


if __name__ == "__main__":
    base = os.path.dirname(__file__)
    extract_pdfs(
        os.path.join(base, "docs_pdf"),
        os.path.join(base, "docs_txt"),
    )
    # 切片测试
    with open(os.path.join(base, "docs_txt", "租房补贴.txt"), "r", encoding="utf-8") as f:
        content = f.read()
    chunks = split_text(content)
    print(f"切分数量：{len(chunks)}，第一个块长度：{len(chunks[0])}")
