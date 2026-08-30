
from pydantic import BaseModel


class ResearchResult (BaseModel):
    key_facts  :list[str]
    summary   :str


class DraftReport(BaseModel):
    title	    :str
    sections	:list[str]
    conclusion	:str


class ReviewResult(BaseModel):
    passed	 : bool
    score	 : int
    feedback : str


if __name__ == "__main__":
    ceshi1=DraftReport(
        title="111",
        sections=["222","333"],
        conclusion="444"

    )
    print(ceshi1.model_dump())