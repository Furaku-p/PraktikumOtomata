import tkinter as tk
from tkinter import ttk, messagebox
import re

LANGUAGE_KEYWORDS = {
    "python": {
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
        "try", "while", "with", "yield", "print"
    },
    "c++": {
        "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand",
        "bitor", "bool", "break", "case", "catch", "char", "class", "compl",
        "const", "constexpr", "const_cast", "continue", "decltype", "default",
        "delete", "do", "double", "dynamic_cast", "else", "enum", "explicit",
        "export", "extern", "false", "float", "for", "friend", "goto", "if",
        "inline", "int", "long", "mutable", "namespace", "new", "noexcept",
        "not", "not_eq", "nullptr", "operator", "or", "or_eq", "private",
        "protected", "public", "register", "reinterpret_cast", "return",
        "short", "signed", "sizeof", "static", "static_cast", "struct",
        "switch", "template", "this", "throw", "true", "try", "typedef",
        "typeid", "typename", "union", "unsigned", "using", "virtual", "void",
        "volatile", "while"
    },
    "c": {
        "auto", "break", "case", "char", "const", "continue", "default",
        "do", "double", "else", "enum", "extern", "float", "for", "goto",
        "if", "int", "long", "register", "return", "short", "signed",
        "sizeof", "static", "struct", "switch", "typedef", "union",
        "unsigned", "void", "volatile", "while"
    },
    "java": {
        "abstract", "assert", "boolean", "break", "byte", "case", "catch",
        "char", "class", "const", "continue", "default", "do", "double",
        "else", "enum", "extends", "final", "finally", "float", "for", "goto",
        "if", "implements", "import", "instanceof", "int", "interface",
        "long", "native", "new", "package", "private", "protected", "public",
        "return", "short", "static", "strictfp", "super", "switch",
        "synchronized", "this", "throw", "throws", "transient", "true",
        "false", "try", "void", "volatile", "while"
    }
}

MULTI_CHAR_SYMBOLS = [
    ">>=", "<<=", "==", "!=", ">=", "<=", "++", "--", "&&", "||",
    "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "->", "::", "<<", ">>"
]

SINGLE_CHAR_SYMBOLS = set(r"+-*/%=><(){}[]:;,.!&|^~#?")

COMMON_NON_VARIABLE_IDENTIFIERS = {
    "cin", "cout", "endl", "printf", "scanf", "main",
    "System", "out", "println", "print",
    "std", "vector", "stack", "queue", "map", "set", "string",
    "max", "min", "top", "push", "pop", "empty", "size"
}


def remove_comments(code, language):
    if language == "python":
        code = re.sub(r"#.*", "", code)
        code = re.sub(r"'''[\s\S]*?'''", "", code)
        code = re.sub(r'"""[\s\S]*?"""', "", code)
    else:
        code = re.sub(r"//.*", "", code)
        code = re.sub(r"/\*[\s\S]*?\*/", "", code)
    return code


def extract_preprocessor(code, language):
    directives = []
    if language in {"c", "c++"}:
        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                directives.append(stripped)
    return directives


def tokenize(code):
    multi = sorted(MULTI_CHAR_SYMBOLS, key=len, reverse=True)
    pattern = (
        r'"(?:\\.|[^"\\])*"'
        r"|'(?:\\.|[^'\\])*'"
        r"|[A-Za-z_][A-Za-z0-9_]*"
        r"|\d+(?:\.\d+)?"
        r"|" + "|".join(re.escape(s) for s in multi) +
        r"|[" + re.escape("".join(SINGLE_CHAR_SYMBOLS)) + r"]"
    )
    return re.findall(pattern, code)


def extract_declared_variables(code, language):
    declared = set()
    lines = code.splitlines()

    if language in {"c", "c++", "java"}:
        type_pattern = re.compile(
            r'\b(?:int|long|short|float|double|char|bool|boolean|String|void|'
            r'unsigned|signed|struct|string|vector|stack|queue|map|set)\b'
        )
        identifier_pattern = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')

        for line in lines:
            if line.strip().startswith("#"):
                continue

            if type_pattern.search(line):
                ids = identifier_pattern.findall(line)
                filtered = []
                for item in ids:
                    if item in LANGUAGE_KEYWORDS[language]:
                        continue
                    if item in COMMON_NON_VARIABLE_IDENTIFIERS:
                        continue
                    filtered.append(item)

                blacklist = {
                    "vector", "stack", "queue", "map", "set", "string",
                    "std", "include", "using", "namespace"
                }
                for item in filtered:
                    if item not in blacklist:
                        declared.add(item)

    elif language == "python":
        assign_pattern = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=')
        for line in lines:
            m = assign_pattern.search(line)
            if m:
                name = m.group(1)
                if name not in LANGUAGE_KEYWORDS[language]:
                    declared.add(name)

    return declared


def extract_math_expressions(code, language):
    expressions = []
    lines = code.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if language in {"c", "c++"} and stripped.startswith("#"):
            continue

        if re.search(r'(\+|-|\*|/|%|==|!=|>=|<=|=|>|<)', stripped):
            if re.match(r'^(cin\s*>>|cout\s*<<|printf\s*\(|scanf\s*\()', stripped):
                continue
            expressions.append(stripped)

    return expressions


def unique(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def analyze_code(code, language):
    cleaned = remove_comments(code, language)
    directives = extract_preprocessor(cleaned, language)
    tokens = tokenize(cleaned)
    keywords = LANGUAGE_KEYWORDS[language]

    reserved_words = []
    symbols = []
    identifiers = []
    variables = []

    declared_variables = extract_declared_variables(cleaned, language)

    for token in tokens:
        if token in keywords:
            reserved_words.append(token)
        elif token in MULTI_CHAR_SYMBOLS or (len(token) == 1 and token in SINGLE_CHAR_SYMBOLS):
            symbols.append(token)
        elif re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', token):
            if token not in keywords:
                identifiers.append(token)
                if token in declared_variables:
                    variables.append(token)

    math_expressions = extract_math_expressions(cleaned, language)

    return {
        "preprocessor": unique(directives),
        "reserved_words": unique(reserved_words),
        "symbols": unique(symbols),
        "variables": unique(variables),
        "identifiers_lain": unique([x for x in identifiers if x not in declared_variables]),
        "math_expressions": unique(math_expressions),
    }


def fill_text(widget, data):
    widget.config(state="normal")
    widget.delete("1.0", tk.END)
    widget.insert(tk.END, "\n".join(data) if data else "-")
    widget.config(state="disabled")


def run_analysis():
    code = input_text.get("1.0", tk.END).strip()
    language = language_var.get()

    if not code:
        messagebox.showwarning("Peringatan", "Masukkan source code terlebih dahulu.")
        return

    result = analyze_code(code, language)

    fill_text(preprocessor_output, result["preprocessor"])
    fill_text(reserved_output, result["reserved_words"])
    fill_text(symbol_output, result["symbols"])
    fill_text(variable_output, result["variables"])
    fill_text(identifier_output, result["identifiers_lain"])
    fill_text(math_output, result["math_expressions"])

    status_var.set(
        f"Analisis selesai | Bahasa: {language} | "
        f"Reserved: {len(result['reserved_words'])} | "
        f"Simbol: {len(result['symbols'])} | "
        f"Variabel: {len(result['variables'])}"
    )


def clear_all():
    input_text.delete("1.0", tk.END)
    for widget in [
        preprocessor_output, reserved_output, symbol_output,
        variable_output, identifier_output, math_output
    ]:
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.config(state="disabled")
    status_var.set("Siap digunakan.")


def create_output_box(parent, title_text, row, col, height=10):
    frame = ttk.LabelFrame(parent, text=title_text, padding=10)
    frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    text_box = tk.Text(
        frame,
        height=height,
        width=36,
        font=("Consolas", 10),
        bg="#f8fafc",
        fg="#1e293b",
        relief="flat",
        wrap="word",
        padx=8,
        pady=8
    )
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_box.yview)
    text_box.configure(yscrollcommand=scrollbar.set)

    text_box.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    text_box.config(state="disabled")
    return text_box


root = tk.Tk()
root.title("Tokenizer Source Code Multibahasa")
root.geometry("1280x820")
root.minsize(1100, 720)
root.configure(bg="#eaf2f8")

style = ttk.Style()
style.theme_use("clam")

style.configure("TFrame", background="#eaf2f8")
style.configure("Header.TFrame", background="#1e3a8a")
style.configure("HeaderTitle.TLabel", background="#1e3a8a", foreground="white", font=("Segoe UI", 18, "bold"))
style.configure("HeaderSub.TLabel", background="#1e3a8a", foreground="#dbeafe", font=("Segoe UI", 10))
style.configure("TLabel", background="#eaf2f8", foreground="#1e293b", font=("Segoe UI", 10))
style.configure("TLabelframe", background="#eaf2f8", foreground="#1e3a8a")
style.configure("TLabelframe.Label", background="#eaf2f8", foreground="#1e3a8a", font=("Segoe UI", 10, "bold"))
style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)
style.configure("Accent.TButton", background="#2563eb", foreground="white")
style.map("Accent.TButton", background=[("active", "#1d4ed8")])

header = ttk.Frame(root, style="Header.TFrame", padding=18)
header.pack(fill="x")

ttk.Label(header, text="Program Analisis Token Source Code", style="HeaderTitle.TLabel").pack(anchor="w")
ttk.Label(
    header,
    text="Menganalisis token berdasarkan bahasa pemrograman: Python, C++, C, dan Java",
    style="HeaderSub.TLabel"
).pack(anchor="w", pady=(4, 0))

main_container = ttk.Frame(root, padding=15)
main_container.pack(fill="both", expand=True)

control_frame = ttk.Frame(main_container)
control_frame.pack(fill="x", pady=(0, 10))

ttk.Label(control_frame, text="Pilih Bahasa:").pack(side="left", padx=(0, 8))

language_var = tk.StringVar(value="c++")
language_combo = ttk.Combobox(
    control_frame,
    textvariable=language_var,
    values=["python", "c++", "c", "java"],
    state="readonly",
    width=15,
    font=("Segoe UI", 10)
)
language_combo.pack(side="left", padx=(0, 12))

ttk.Button(control_frame, text="Analisis", command=run_analysis, style="Accent.TButton").pack(side="left", padx=5)
ttk.Button(control_frame, text="Bersihkan", command=clear_all).pack(side="left", padx=5)

input_frame = ttk.LabelFrame(main_container, text="Input Source Code", padding=10)
input_frame.pack(fill="both", expand=False, pady=(0, 12))

input_text_frame = ttk.Frame(input_frame)
input_text_frame.pack(fill="both", expand=True)

input_text = tk.Text(
    input_text_frame,
    height=14,
    font=("Consolas", 11),
    bg="#f8fafc",
    fg="#0f172a",
    insertbackground="#0f172a",
    relief="flat",
    wrap="none",
    padx=10,
    pady=10
)

input_scroll_y = ttk.Scrollbar(input_text_frame, orient="vertical", command=input_text.yview)
input_scroll_x = ttk.Scrollbar(input_text_frame, orient="horizontal", command=input_text.xview)
input_text.configure(yscrollcommand=input_scroll_y.set, xscrollcommand=input_scroll_x.set)

input_text.grid(row=0, column=0, sticky="nsew")
input_scroll_y.grid(row=0, column=1, sticky="ns")
input_scroll_x.grid(row=1, column=0, sticky="ew")

input_text_frame.rowconfigure(0, weight=1)
input_text_frame.columnconfigure(0, weight=1)

output_frame = ttk.Frame(main_container)
output_frame.pack(fill="both", expand=True)

for r in range(2):
    output_frame.rowconfigure(r, weight=1)
for c in range(3):
    output_frame.columnconfigure(c, weight=1)

preprocessor_output = create_output_box(output_frame, "Preprocessor", 0, 0)
reserved_output = create_output_box(output_frame, "Reserved Words", 0, 1)
symbol_output = create_output_box(output_frame, "Simbol dan Tanda Baca", 0, 2)
variable_output = create_output_box(output_frame, "Variabel", 1, 0)
identifier_output = create_output_box(output_frame, "Identifier Lain", 1, 1)
math_output = create_output_box(output_frame, "Kalimat Matematika", 1, 2)

status_var = tk.StringVar(value="Siap digunakan.")
status_bar = ttk.Label(root, textvariable=status_var, anchor="w", relief="sunken", padding=8)
status_bar.pack(fill="x", side="bottom")

root.mainloop()