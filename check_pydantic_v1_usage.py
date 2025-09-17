import os
import re

# Padrões do Pydantic v1 que precisam ser atualizados
PATTERNS = {
    r"\.dict\(": "Use `.model_dump()` em vez de `.dict()`",
    r"\.json\(": "Use `.model_dump_json()` em vez de `.json()`",
    r"parse_obj": "Use `.model_validate()` em vez de `parse_obj`",
    r"from pydantic\.generics import GenericModel": "Substitua GenericModel por BaseModel + typing.Generic",
    r"class Config:": "Troque Config por model_config (ou ConfigDict) no Pydantic v2",
}

def scan_file(filepath):
    issues = []
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            for pattern, message in PATTERNS.items():
                if re.search(pattern, line):
                    issues.append((i, line.strip(), message))
    return issues

def scan_project(root="."):
    results = {}
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                issues = scan_file(filepath)
                if issues:
                    results[filepath] = issues
    return results

if __name__ == "__main__":
    results = scan_project(".")
    if not results:
        print("✅ Nenhum uso antigo do Pydantic v1 encontrado. Projeto já parece compatível com Pydantic v2.")
    else:
        print("⚠️ Encontrados pontos que precisam ser migrados:")
        for filepath, issues in results.items():
            print(f"\n📂 Arquivo: {filepath}")
            for line_no, line, msg in issues:
                print(f"  Linha {line_no}: {line}")
                print(f"    👉 {msg}")
