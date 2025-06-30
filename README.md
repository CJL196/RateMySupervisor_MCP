# RateMySupervisor_MCP

`RateMySupervisor_MCP` 是一个基于 FastMCP 构建的服务器，提供了一个接口，用于查询来自[导师评价网](https://www.urfire.com/)的导师评价数据。大语言模型（LLM）或其他兼容 MCP 协议的客户端可以通过此服务器轻松地获取导师、院系和评价信息。

## 数据来源

数据来源：[https://github.com/pengp25/RateMySupervisor](https://github.com/pengp25/RateMySupervisor)，这个仓库使用了爬虫工具从[导师推荐网](https://www.urfire.com/)获取导师评价数据，存储为`data/comments_data.json`。

`comments_data.json`存储了如下格式的`json`数据：
```json
[
  {
    "school_cate": "", 
    "university": "", 
    "department": "", 
    "supervisor": "", 
    "rate": 0, 
    "description": ""
  }
]
```

## 安装与运行

1.  **克隆仓库**
    ```bash
    git clone https://github.com/CJL196/RateMySupervisor_MCP.git
    cd RateMySupervisor_MCP
    ```

2.  **安装依赖**
    项目依赖 `fastmcp` 和 `pydantic`。通过以下命令安装：
    ```bash
    pip install -r requirements.txt
    ```

3.  **运行服务器**
    直接运行 `server.py` 即可启动 MCP 服务器：
    ```bash
    python server.py
    ```
    服务器将以 MCP Stdio 模式运行，等待客户端连接。

## MCP 客户端配置

要将此服务器集成到兼容 MCP 的客户端（如cursor或cline）中，您可以使用类似以下的配置。请确保将 `command` 和 `args` 中的路径修改为 `server.py` 在您系统中的 **绝对路径**。

```json
{
  "mcpServers": {
    "RateMySupervisor": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "python",
      "args": [
        "/path/to/your/RateMySupervisor_MCP/server.py"
      ],
      "env": {}
    }
  }
}
```

## 可用工具 (API)

服务器 `(name="导师评价查询系统")` 提供了以下工具：

---

### 1. `search_supervisor_by_name`

根据导师姓名模糊搜索相关的评价。

-   **参数**:
    -   `name` (string, required): 要搜索的导师姓名。
-   **成功响应**:
    ```json
    {
      "success": true,
      "data": [
        {
          "school_cate": "985",
          "university": "哈尔滨工业大学",
          "department": "机电工程学院",
          "supervisor": "周裕(深圳,千人计划)",
          "rate": 2.5,
          "description": "自证认识导师：57年生人...\n学术水平：喜欢发高质量论文..."
        }
      ]
    }
    ```
-   **失败响应**:
    ```json
    {
      "success": false,
      "message": "没有找到名为 '张三' 的导师。"
    }
    ```

---
### 2. `get_departments_by_university`

根据大学名称，获取该大学所有的院系列表。

-   **参数**:
    -   `university` (string, required): 要查询的大学名称，支持模糊匹配。
-   **成功响应**:
    ```json
    {
      "success": true,
      "data": [
        "机电工程学院",
        "计算机科学与技术学院"
      ]
    }
    ```
-   **失败响应**:
    ```json
    {
      "success": false,
      "message": "没有找到大学 '未知大学' 的信息或该大学下没有院系列表。"
    }
    ```

---
### 3. `get_supervisors_by_university_and_department`

根据大学和院系名称，获取该院系所有的导师列表。

-   **参数**:
    -   `university` (string, required): 大学名称，支持模糊匹配。
    -   `department` (string, required): 院系名称，支持模糊匹配。
-   **成功响应**:
    ```json
    {
      "success": true,
      "data": [
        "杨立军",
        "白基成",
        "郝明晖"
      ]
    }
    ```
-   **失败响应**:
    ```json
    {
      "success": false,
      "message": "在 '哈尔滨工业大学' 的 '未知学院' 没有找到导师信息。"
    }
    ```

---
### 4. `get_reviews`

根据大学、院系和导师的完整信息，获取具体评价。

-   **参数**:
    -   `university` (string, required): 大学名称，支持模糊匹配。
    -   `department` (string, required): 院系名称，支持模糊匹配。
    -   `supervisor` (string, required): 导师姓名，支持模糊匹配。
-   **成功响应**:
    ```json
    {
      "success": true,
      "data": [
        {
          "school_cate": "985",
          "university": "哈尔滨工业大学",
          "department": "机电工程学院",
          "supervisor": "杨立军",
          "rate": 5.0,
          "description": "自证认识导师：办公室在制造楼5楼..."
        }
      ]
    }
    ```
-   **失败响应**:
    ```json
    {
      "success": false,
      "message": "没有找到关于 '哈尔滨工业大学' '机电工程学院' 的 '王五' 导师的评价。"
    }
    ```

</rewritten_file>