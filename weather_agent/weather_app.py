import streamlit as st
from weather_agent import agent, WeatherState  # 导入昨天的agent

st.set_page_config(page_title="AI穿衣助手", page_icon="☀️")
st.title("👔 AI穿衣建议助手")

city = st.text_input("请输入城市名称（如：南昌）", value="")

if st.button("获取今日穿搭建议"):
    if not city.strip():
        st.warning("请先输入城市名称")
    else:
        with st.spinner("正在获取天气并生成建议..."):
            init = {"city": city, "weather_data": "", "suggestion": "", "history": []}
            result = agent.invoke(init)
            st.success("建议生成！")
            st.markdown(f"**{city}今日建议**：{result['suggestion']}")
            if result['history']:
                st.subheader("历史建议")
                for h in result['history']:
                    st.write(h)
