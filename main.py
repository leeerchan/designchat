import sys
import time
import streamlit as st
from crewai import Agent, Task, Crew, Process
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import Tool
from langchain_openai import ChatOpenAI
import os
import re

st.set_page_config(page_title='产品设计小帮手')

llm = ChatOpenAI(
    temperature=0.95,
    model="gpt-4",
    openai_api_key="sk-proj-1NZyBk9m6pwhc4kaTBJ2T3BlbkFJUl0OL4Kgr6U5JVqX84JG",
    openai_api_base="https://api.openai.com/v1/"
    )
# llm = ChatOpenAI(
#       temperature=0.95,
#       model='glm-3-turbo',
#       base_url="https://open.bigmodel.cn/api/paas/v4/",
#       api_key="91d43e7739139e68454951178b3c700d.ltHi2UmAKMfa0xqZ"
#     )

duckduckgo_search = DuckDuckGoSearchRun()

# 追踪代理执行的任务
task_values = []


def create_crewai_setup(product_name):
    market_research_analyst = Agent(
        role="市场调研分析员",
        goal=f"""分析{product_name}的市场需求并制定市场策略""",
        backstory=f"""擅长了解产品（如 {product_name}）的市场需求、目标受众和竞争情况。
                      善于制定营销战略以覆盖广泛的受众。""",
        verbose=True,
        allow_delegation=True,
        tools=[duckduckgo_search],
        llm=llm,
    )
    technology_expert = Agent(
        role="技术专家",
        goal=f"评估生产高质量{product_name}的技术可行性和要求",
        backstory=f"""对当前和新兴技术趋势有远见、特别是在{product_name}等产品方面。
                      确定哪些技术最适合不同的业务模式。""",
        verbose=True,
        allow_delegation=True,
        llm=llm,
    )
    product_designer = Agent(
        role="产品设计师",
        goal=f"设计符合市场需求且具有竞争力的{product_name}",
        backstory=f"""具备出色的视觉设计能力和用户研究背景，专注于创造满足用户需求和市场趋势的{product_name}。
                      能够将设计理念转化为实际产品，并确保设计在功能和美学上的平衡。""",
        verbose=True,
        allow_delegation=True,
        llm=llm,
    )

    task1 = Task(
        description=f"""对{product_name}进行市场调研，给出该产品的设计建议。""",
        expected_output="市场调研报告。",
        agent=market_research_analyst,
    )
    task2 = Task(
        description=f"""分析生成高质量{product_name}的重要因素，并给出设计建议。""",
        expected_output="生产技术报告。",
        agent=technology_expert,
    )

    product_crew = Crew(
        agents=[market_research_analyst, technology_expert, product_designer],
        # tasks=[task1, task2],
        tasks=[task1],
        verbose=2,
        process=Process.sequential,
    )
    crew_result = product_crew.kickoff()
    return crew_result


# Sidebar for accepting input parameters
with st.sidebar:
    st.header("团队")
    with st.expander("市场调研分析员"):
        st.text("""       
        目标 = 分析{product_name}的市场需求并制定市场策略
        背景 = 擅长了解产品（如 {product_name}）的市场需求、目标受众和竞争情况。
              善于制定营销战略以覆盖广泛的受众""")
    with st.expander("技术专家"):
        st.text("""       
        目标 = 评估生产高质量{product_name}的技术可行性和要求
        背景 = 对当前和新兴技术趋势有远见、特别是在{product_name}等产品方面。
              确定哪些技术最适合不同的业务模式。""")
    with st.expander("产品设计师"):
        st.text("""       
        目标 = 设计符合市场需求且具有竞争力的{product_name}
        背景 = 具备出色的视觉设计能力和用户研究背景，专注于创造满足用户需求和市场趋势的{product_name}。
              能够将设计理念转化为实际产品，并确保设计在功能和美学上的平衡。""")

    st.header("任务")
    st.text("1. 对{product_name}进行市场调研，给出该产品需要关注的维度和销售趋势。")
    # st.text("2. 分析生成高质量{product_name}的重要因素，并给出设计建议。")


class StreamToExpander:
    def __init__(self, expander):
        self.expander = expander
        self.buffer = []
        self.colors = ['red', 'green', 'blue', 'orange']  # Define a list of colors
        self.color_index = 0  # Initialize color index

    def write(self, data):
        # Filter out ANSI escape codes using a regular expression
        cleaned_data = re.sub(r'\x1B\[[0-9;]*[mK]', '', data)

        # Check if the data contains 'task' information
        task_match_object = re.search(r'\"任务\"\s*:\s*\"(.*?)\"', cleaned_data, re.IGNORECASE)
        task_match_input = re.search(r'任务\s*:\s*([^\n]*)', cleaned_data, re.IGNORECASE)
        task_value = None
        if task_match_object:
            task_value = task_match_object.group(1)
        elif task_match_input:
            task_value = task_match_input.group(1).strip()

        if task_value:
            st.toast(":robot_face: " + task_value)

        # Check if the text contains the specified phrase and apply color
        if "Entering new CrewAgentExecutor chain" in cleaned_data:
            # Apply different color and switch color index
            self.color_index = (self.color_index + 1) % len(
                self.colors)  # Increment color index and wrap around if necessary

            cleaned_data = cleaned_data.replace("Entering new CrewAgentExecutor chain",
                                                f":{self.colors[self.color_index]}[Entering new CrewAgentExecutor chain]")

        if "市场调研分析员" in cleaned_data:
            # Apply different color 
            cleaned_data = cleaned_data.replace("市场调研分析员",
                                                f":{self.colors[self.color_index]}[市场调研分析员]")
        if "技术专家" in cleaned_data:
            cleaned_data = cleaned_data.replace("技术专家",
                                                f":{self.colors[self.color_index]}[技术专家]")
        if "产品设计师" in cleaned_data:
            cleaned_data = cleaned_data.replace("产品设计师",
                                                f":{self.colors[self.color_index]}[产品设计师]")
        if "Finished chain." in cleaned_data:
            cleaned_data = cleaned_data.replace("Finished chain.", f":{self.colors[self.color_index]}[Finished chain.]")

        self.buffer.append(cleaned_data)
        if "\n" in data:
            self.expander.markdown(''.join(self.buffer), unsafe_allow_html=True)
            self.buffer = []


# Streamlit interface
def run_crewai_app():
    st.title('🤖产品设计小帮手')

    product_name = st.text_input("请输入你想要设计的产品")

    if st.button("开始分析"):
        # Placeholder for stopwatch
        stopwatch_placeholder = st.empty()

        # Start the stopwatch
        start_time = time.time()
        with st.expander("进行中!"):
            sys.stdout = StreamToExpander(st)
            with st.spinner("生成结果中"):
                crew_result = create_crewai_setup(product_name)

        # Stop the stopwatch
        end_time = time.time()
        total_time = end_time - start_time
        stopwatch_placeholder.text(f"Total Time Elapsed: {total_time:.2f} seconds")

        st.header("Tasks:")
        st.table({"Tasks": task_values})

        st.header("Results:")
        st.markdown(crew_result)


if __name__ == "__main__":
    run_crewai_app()