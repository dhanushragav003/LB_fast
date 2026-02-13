from app.schemas.email import BiteEmail
from pydantic import ValidationError
from typing import Tuple
import re
import markdown
from markupsafe import Markup, escape
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

TEMPLATE_DIR = Path("app/templates")

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def smart_render(text: str) -> Markup:
    import re, markdown
    from markupsafe import Markup, escape

    if not text:
        return Markup("")

    # Treat numbered lines as Markdown by always converting numbered lists
    markdown_patterns = [
            r"\*\*.*?\*\*",
            r"\*.*?\*",
            r"`.*?`",
            r"^#{1,6} ",
            r"```",
            r"~~.*?~~",
            r"\[.*?\]\(.*?\)",
            r"^\d+\.\s"   # <- detect numbered lists
        ]

    if any(re.search(pat, text, re.MULTILINE) for pat in markdown_patterns):
        html = markdown.markdown(
            text,
            extensions=["fenced_code", "codehilite", "sane_lists"]
        )
        return Markup(html)
    else:
        return Markup(escape(text))

def render_email(template_name: str, context: dict) -> str:
    """
    Renders an HTML email template with Jinja2.
    """
    for key, value in context.items():
        if isinstance(value, str) and value.strip():
            context[key] = smart_render(value)
    
    template = jinja_env.get_template(template_name)
    return template.render(**context)
# def render_email(template_name: str, context: dict) -> str:
#     template = jinja_env.get_template(template_name)
#     return template.render(**context)

def construct_mail(bitemail:BiteEmail,redirect_url=None) -> Tuple[str, str]:
    email_subject=bitemail.email_subject
    params = {
        **bitemail.model_dump(),
        "play_url": redirect_url,
    }
    html_str= render_email("bite_email.html",params)
    return email_subject , html_str
def get_completed_mail(title:str,completed_chapters:int,redirect_url:str)-> Tuple[str, str]:
    subject =f"{title} — Learning Progress Update 🎉"
    params={ "title":title,"completed_chapters":completed_chapters,"play_url":redirect_url}
    html_str= render_email("completed.html",params)
    return subject, html_str

def validate_generated_email(generated_content) -> BiteEmail:
    try:
        clean_str = generated_content.strip()
        if clean_str.startswith("```"):
            # Remove opening and closing backticks/language tags
            clean_str = clean_str.split("json")[-1].strip("`").strip()
        email_data = BiteEmail.model_validate_json(clean_str)
        return email_data
    except (ValidationError, ValueError) as e:
        error_msg = (
        "Generated JSON failed schema validation.\n"
        f"Details:\n{e.json()}"
        )
        raise ValueError(error_msg) from e