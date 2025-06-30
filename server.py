import json
from fastmcp import FastMCP
from typing import List, Dict, Any
from pydantic import Field
from typing import Annotated
import sys
import os
import pinyin

# Helper function to check for Chinese characters
def _contains_chinese(text: str) -> bool:
    """Checks if a string contains any Chinese characters."""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def _is_supervisor_match(query_name: str, supervisor_in_data: str) -> bool:
    """
    Checks if a query name matches a supervisor name from data.
    Handles direct substring match and pinyin match for Chinese queries.
    """
    if not query_name or not supervisor_in_data:
        return False
        
    query_lower = query_name.lower()
    target_lower = supervisor_in_data.lower()

    # 1. Direct substring match
    if query_lower in target_lower:
        return True

    # 2. If query is Chinese, try pinyin match
    if _contains_chinese(query_name):
        # pinyin.get returns pinyin parts, e.g., 'he', 'kai', 'ming'
        # This handles cases like "Kaiming He" vs "He Kaiming"
        pinyin_parts = pinyin.get(query_name, format="strip", delimiter="-").split('-')
        if all(part in target_lower for part in pinyin_parts):
            return True
    
    return False

# Construct path to data file relative to the script to ensure it's always found
script_dir = os.path.dirname(os.path.abspath(__file__))
data_file_path = os.path.join(script_dir, 'data', 'comments_data.json')

# Load data
try:
    with open(data_file_path, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
except FileNotFoundError:
    print(f"Error: Data file not found at '{data_file_path}'")
    print("Please ensure 'comments_data.json' is located in a 'data' directory next to the script.")
    sys.exit(1)

app = FastMCP(
    name="RateMySupervisor_MCP",
    instructions="""你是一个用于查询导师评价的助手。你的任务是根据用户的请求，调用合适的工具来查询导师信息。请遵循以下步骤和格式要求以确保查询的准确性：

1.  **明确查询意图与推荐工作流**:
    *   如果用户只提供了大学名称，你的首要任务是调用 `get_departments_by_university` 工具，获取该大学的官方院系列表，并展示给用户以供选择。
    *   如果用户提供了大学和院系，你应该调用 `get_supervisors_by_university_and_department` 来获取该院系下的导师列表。
    *   当用户提供了明确的大学、院系和导师信息，或希望获取某个导师的详细评价时，最终应调用 `get_reviews` 工具。
    *   如果用户仅按姓名搜索导师，可以使用 `search_supervisor_by_name`，但这可能返回多个学校的结果，应提示用户此点。

2.  **严格遵守输入格式**:
    *   **大学名称**: 必须使用官方的中文全称。例如，将用户的"北大"、"pku"或"Peking University"转换为"北京大学"再进行查询。
    *   **导师姓名**: 对于中国大陆的院校，请使用导师的简体中文姓名。对于其他地区（如香港、澳门、台湾及海外）的院校，请使用其常用的英文名（例如，将"何凯明"转换为"Kaiming He"）。
    *   **院系名称**: 强烈建议使用从 `get_departments_by_university` 工具返回的官方院系名称，以避免因名称不匹配（如"计算机系"与"计算机科学与技术学院"）导致的查询失败。

3.  **与用户交互**:
    *   当信息不足时，主动向用户询问缺失的信息（例如，在获得院系列表后，询问用户想查询哪个院系）。
    *   当查询没有结果时，向用户说明情况，并可以建议用户放宽条件或检查输入是否正确。"""
)

def clean_review(review: Dict[str, Any]) -> Dict[str, Any]:
    """Cleans the description field of a review."""
    cleaned_review = review.copy()
    description = cleaned_review.get('description', '')
    if isinstance(description, str):
        cleaned_review['description'] = description.replace('<br><br>', '\n').replace('<br>', '\n')
    return cleaned_review

@app.tool
def search_supervisor_by_name(
    name: Annotated[str, Field(description="要搜索的导师姓名")]
) -> Dict[str, Any]:
    """
    根据导师姓名搜索相关的所有评价。
    为保证查询准确性，请提供导师的完整姓名。对于中国大陆院校的导师，请使用中文名；对于非中国大陆院校的导师，请使用其常用英文名（例如 'Kaiming He'）。
    """
    results = []
    seen_entries = set()
    for entry in all_data:
        # Use frozenset of items to make the dict hashable for the 'seen' set
        entry_tuple = frozenset(entry.items())
        if entry_tuple in seen_entries:
            continue
            
        if _is_supervisor_match(name, entry.get('supervisor', '')):
            results.append(clean_review(entry))
            seen_entries.add(entry_tuple)

    if not results:
        return {"success": False, "message": f"没有找到与 '{name}' 相关的导师。"}
    
    return {"success": True, "data": results}

@app.tool
def get_departments_by_university(
    university: Annotated[str, Field(description="要查询的大学名称")]
) -> Dict[str, Any]:
    """
    给定大学名称，查看该大学有哪些院系。
    请务必使用大学的官方中文全称进行查询（例如：请将"北大"或"Peking"转换为"北京大学"）。
    此工具可以帮助您获取后续查询所需的标准院系名。
    """
    departments = set()
    for entry in all_data:
        if university.lower() in entry.get('university', '').lower():
            department = entry.get('department')
            if department:
                departments.add(department)
    
    if not departments:
        return {"success": False, "message": f"没有找到大学 '{university}' 的信息或该大学下没有院系列表。"}
        
    return {"success": True, "data": sorted(list(departments))}

@app.tool
def get_supervisors_by_university_and_department(
    university: Annotated[str, Field(description="大学名称")],
    department: Annotated[str, Field(description="院系名称")]
) -> Dict[str, Any]:
    """
    给定大学和院系的名称，查看有哪些导师。
    为确保结果准确，建议先通过 `get_departments_by_university` 工具查询并使用返回的官方院系名称。
    大学名称同样需要使用官方中文全称。
    """
    supervisors = set()
    for entry in all_data:
        if (university.lower() in entry.get('university', '').lower() and
                department.lower() in entry.get('department', '').lower()):
            supervisor = entry.get('supervisor')
            if supervisor:
                supervisors.add(supervisor)
            
    if not supervisors:
        return {"success": False, "message": f"在 '{university}' 的 '{department}' 没有找到导师信息。"}
        
    return {"success": True, "data": sorted(list(supervisors))}

@app.tool
def get_reviews(
    university: Annotated[str, Field(description="大学名称")],
    department: Annotated[str, Field(description="院系名称")],
    supervisor: Annotated[str, Field(description="导师姓名")]
) -> Dict[str, Any]:
    """
    给定大学、院系和导师的名称，查看具体评价。
    为获得最精确的结果，请务必遵循以下格式：
    1.  **大学**: 使用官方中文全称 (例如: '北京大学')。
    2.  **院系**: 使用通过 `get_departments_by_university` 查询到的官方名称。
    3.  **导师**: 中国大陆院校使用中文名, 其他地区使用英文名 (例如: 'Kaiming He')。
    """
    results = [
        clean_review(entry) for entry in all_data 
        if (university.lower() in entry.get('university', '').lower() and
            department.lower() in entry.get('department', '').lower() and
            _is_supervisor_match(supervisor, entry.get('supervisor', '')))
    ]
    
    if not results:
        return {"success": False, "message": f"没有找到关于 '{university}' '{department}' 的 '{supervisor}' 导师的评价。"}
        
    return {"success": True, "data": results}

if __name__ == "__main__":
    app.run()
