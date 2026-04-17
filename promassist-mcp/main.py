import os
import uuid
import datetime
import docx
from weasyprint import HTML 
from jinja2 import Environment, FileSystemLoader
from mcp.server.fastmcp import FastMCP
from atlassian import Jira

# Конфигурация Jira
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_URL")

jira = Jira(url=JIRA_URL, username=JIRA_EMAIL, password=JIRA_TOKEN, cloud=True)

mcp = FastMCP("PromAssist_Service", stateless_http=True, host='0.0.0.0', port=8000)
env = Environment(loader=FileSystemLoader('.'))
DOCS_DIR = "/app/generated_docs"
os.makedirs(DOCS_DIR, exist_ok=True)

@mcp.tool()
def register_idea_jira(title: str, description: str, author: str, project_key: str = "PROJ") -> str:
    """Регистрация задачи в реальной Jira."""
    try:
        new_issue = jira.issue_create(fields={
            'project': {'key': project_key},
            'summary': f"Идея: {title}",
            'description': f"Автор: {author}\nОписание: {description}",
            'issuetype': {'name': 'Task'}
        })
        return f"Задача успешно создана! Ссылка: {JIRA_URL}/browse/{new_issue['key']}"
    except Exception as e:
        return f"Ошибка Jira: {str(e)}"

@mcp.tool()
def generate_passport_pdf(full_name: str, enterprise: str, project_manager: str, goal: str, budget: str, economic_effect: str) -> str:
    """Генерирует PDF паспорт со всеми полями (Бюджет, Руководитель, Эффект)."""
    try:
        template = env.get_template('template.html')
        html_out = template.render(
            full_name=full_name, 
            enterprise=enterprise, 
            project_manager=project_manager, 
            goal=goal, 
            budget=budget, 
            economic_effect=economic_effect
        )
        filename = f"Passport_{uuid.uuid4().hex[:6]}.pdf"
        path = os.path.join(DOCS_DIR, filename)
        # Генерация через WeasyPrint для стабильности в Docker
        HTML(string=html_out).write_pdf(path)
        return f"PDF паспорт успешно создан: {filename}"
    except Exception as e:
        return f"Ошибка генерации PDF: {str(e)}"

@mcp.tool()
def generate_passport_docx(short_name: str, full_name: str, enterprise: str, manager: str, goal: str, budget: str) -> str:
    """Создает Паспорт проекта в Word (.docx)."""
    doc = docx.Document()
    doc.add_heading('ПАСПОРТ ПРОЕКТА', 0)
    
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    data = {
        "Краткое наименование": short_name,
        "Полное наименование": full_name,
        "Предприятие": enterprise,
        "Руководитель": manager,
        "Цель": goal,
        "Бюджет": budget
    }
    for key, value in data.items():
        row = table.add_row().cells
        row[0].text = key
        row[1].text = str(value)

    filename = f"Passport_{uuid.uuid4().hex[:6]}.docx"
    doc.save(os.path.join(DOCS_DIR, filename))
    return f"Word документ сохранен: {filename}"

@mcp.tool()
def generate_protocol_txt(session_date: str, participants: str, issues: str, decisions: str) -> str:
    """Создает Протокол сессии решения проблем в TXT."""
    content = f"ПРОТОКОЛ СЕССИИ\nДата: {session_date}\nУчастники: {participants}\n\nПроблемы:\n{issues}\n\nРешения:\n{decisions}"
    filename = f"Protocol_{uuid.uuid4().hex[:4]}.txt"
    with open(os.path.join(DOCS_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)
    return f"Протокол TXT создан: {filename}"

if __name__ == "__main__":
    os.environ["FASTMCP_HOST"] = "0.0.0.0"
    os.environ["FASTMCP_PORT"] = "8000"
    mcp.run(transport='streamable-http')
