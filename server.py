import json
from fastmcp import FastMCP
from typing import List, Dict, Any
from pydantic import Field
from typing import Annotated
import sys
import os

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

app = FastMCP(name="导师评价查询系统")

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
    """
    results = [
        clean_review(entry) for entry in all_data 
        if name.lower() in entry.get('supervisor', '').lower()
    ]
    if not results:
        return {"success": False, "message": f"没有找到名为 '{name}' 的导师。"}
    
    return {"success": True, "data": results}

@app.tool
def get_departments_by_university(
    university: Annotated[str, Field(description="要查询的大学名称")]
) -> Dict[str, Any]:
    """
    给定大学名称，查看该大学有哪些院系。
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
    """
    results = [
        clean_review(entry) for entry in all_data 
        if (university.lower() in entry.get('university', '').lower() and
            department.lower() in entry.get('department', '').lower() and
            supervisor.lower() in entry.get('supervisor', '').lower())
    ]
    
    if not results:
        return {"success": False, "message": f"没有找到关于 '{university}' '{department}' 的 '{supervisor}' 导师的评价。"}
        
    return {"success": True, "data": results}

if __name__ == "__main__":
    app.run()
