def chunk_text(text:str,max_chars:int = 500) ->list[str]:
    """把文本按段落切成块,每块不超过max_chars字。"""
    chunks=[]
    for para in text.split("\n\n"):
        para=para.strip()
        if not para:
            continue
        #"段落太长就按句子硬切"
        while len(para) > max_chars:
            cut=para.rfind("。",0,max_chars)
            if cut == -1:
                cut = max_chars
            chunks.append(para[:cut+1])
            para = para[cut+1:].strip()
        chunks.append(para)
    return chunks


from pathlib import Path

if __name__ == "__main__":
    for path in Path("rag/knowledge").glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        print(f"{path.name}: {len(chunks)} 块")

