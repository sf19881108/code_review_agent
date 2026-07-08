from langchain_core.messages import HumanMessage

from component_assembly import review_app


# 读取整个文件内容
with open('static_review_test.py', 'r', encoding='utf-8') as f:
    sample_code = f.read()
    print(sample_code)

# # 逐行读取（适合大文件，节省内存）
# with open('example.py', 'r', encoding='utf-8') as f:
#     for line in f:
#         print(line.strip()) # strip() 去除每行末尾的换行符
#

result = review_app.invoke(
    {
        "messages": [HumanMessage(content="请审查这段 Python 代码")],
        "code": sample_code,
    }
)

print(result["final_report"])

#利用streamlit展示结果, 并允许用户交互
#增加代码语法检查功能
#进一步增加文件类型的处理
#增加文件批量处理功能，支持上传项目文件进行审查
