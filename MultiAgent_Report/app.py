import streamlit as st
from graph.workflow import app
st.title("多智能体报告系统")
topic=st.text_input("请输入报告主题",value="ai行业趋势 2026")

if st.button("开始生成报告"):
    state={
        "topic":topic,
        "research_notes":"",
        "draft":"",
        "feedback":"",
        "passed":"False",
        "final_report":"",
        "revision_count":0,
    }
    box_researcher=st.status("研究员：等待")
    box_writer=st.status("写作员：等待")
    box_reviewer=st.status("审核员：等待")
    collected={}
    for event in app.stream(state):
        for key,value in event.items():
            collected[key]=value
            if key =="researcher":
                box_researcher.update(label="研究员：完成",state="complete")
                st.write("✅ 资料已整理")
            elif key=="writer":
                box_writer.update(label="写作员：完成",state="complete")
                st.write("✅ 草稿已写出")
            elif key == "reviewer":
                box_reviewer.update(label="审核员：完成", state="complete")
                st.write("✅ 审核完成")
    #流水线跑完了，展示成果
    st.divider()
    notes=collected.get("researcher",{}).get("research_notes","(无)")
    draft=collected.get("writer",{}).get("draft","无")
    feedback=collected.get("reviewer",{}).get("feedback","无")
    with st.expander("研究资料"):
        st.write(notes)
    with st.expander("报告草稿"):
        st.write(draft)
    with st.expander("审核意见"):
        st.write(feedback)