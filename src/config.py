"""Shared paths and hand-curated lists for the analysis."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIGURES = ROOT / "figures"

INNOVATION_GRAPH_URL = (
    "https://raw.githubusercontent.com/github/innovationgraph/main/data/languages.csv"
)
LINGUIST_URL = (
    "https://raw.githubusercontent.com/github-linguist/linguist/main/lib/linguist/languages.yml"
)

# Linguist calls these "programming" languages, but they are build/config/installer
# formats rather than languages people would want a model for.
EXCLUDED = {
    "Dockerfile", "Makefile", "CMake", "Procfile", "Meson", "QMake", "M4", "M4Sugar",
    "Inno Setup", "NSIS", "BitBake", "GDB", "Module Management System",
    "Filebench WML", "Earthly", "Singularity", "RPC", "Linker Script",
}

# SQL dialects are folded into a single "SQL" entry, because on Hugging Face
# almost everything SQL-related is tagged generically (sql, text-to-sql, ...).
SQL_DIALECTS = {"SQL", "PLpgSQL", "TSQL", "PLSQL", "SQLPL", "HiveQL"}

# The "dead languages" of programming: old languages with few active GitHub
# developers today, the analogue of Latin / Ancient Greek in the talk.
LEGACY = {
    "COBOL", "Fortran", "Pascal", "Ada", "Smalltalk", "BASIC", "Visual Basic 6.0",
    "Modula-2", "Modula-3", "REXX", "RPGLE", "Forth", "Classic ASP", "ActionScript",
    "Eiffel", "ABAP", "Common Lisp", "Prolog", "VBA", "CoffeeScript",
}

# Extra Hugging Face tags per language, on top of the name and Linguist aliases.
EXTRA_TAGS = {
    "SQL": ["sql", "text-to-sql", "text2sql", "nl2sql", "t-sql", "pl-sql", "mysql",
            "postgresql", "sqlite", "spider"],
    "Go": ["golang"],
    "C#": ["c-sharp", "csharp", "dotnet"],
    "C++": ["cpp", "cplusplus"],
    "JavaScript": ["javascript", "js", "nodejs"],
    "Shell": ["bash", "shell-script", "shell-commands", "nl2bash"],
    "Verilog": ["rtl", "verilog-generation"],
    "Lean": ["lean4", "lean-4", "lean3"],
    "Coq": ["rocq"],
    "Solidity": ["smart-contracts", "smart-contract"],
    "Assembly": ["asm", "assembly-code"],
    "R": ["rstats", "r-language"],
    "C": ["c-language", "clang"],
}

# Tags that collide with ordinary words, natural-language codes, or are simply too
# short to mean "this programming language" on their own. A model/dataset only
# counts for these when it is ALSO tagged as being about code (see CODE_TAGS) or
# with another, unambiguous programming-language tag.
AMBIGUOUS = {
    "hack", "mako", "red", "io", "e", "j", "m", "q", "v", "d", "r", "c", "cool", "clean",
    "slash", "max", "logos", "limbo", "arc", "turing", "ink", "berry", "pike", "fluent",
    "move", "stan", "euphoria", "cadence", "sage", "faust", "alloy", "squirrel",
    "papyrus", "nasal", "janet", "elvish", "jasmin", "boogie", "puppet", "mercury",
    "dm", "txl", "terra", "idl", "flux", "zap", "nu", "ecl", "al", "eiffel", "clarity",
    "processing", "assembly", "julia", "dart", "swift", "ruby", "rust", "go", "lean",
    "reason", "crystal", "elm", "gleam", "odin", "vala", "zig", "agda", "gap", "m",
    "fennel", "pawn", "metal", "smali", "yacc", "lex", "sed", "awk", "node", "emacs",
    "cake", "cakescript", "max/msp", "nim", "ada", "lua", "sh", "ts", "pl", "hy", "ml",
    "as", "bash", "spider", "rtl", "asm", "clang", "dotnet", "cpp", "lisp", "scheme",
    "prolog", "basic", "forth", "pascal", "apex", "motoko", "ballerina", "haxe", "csound",
    "chuck", "lasso", "rexx", "dafny", "idris", "bluespec", "pony", "racket", "cue",
    "nix", "stata", "sas", "mathematica", "matlab", "ampl", "gams", "modelica", "lilypond",
    "supercollider", "jq", "llvm", "mlir", "webassembly", "wasm", "cuda", "inc", "rake", "posh",
    "bat", "batch", "envrc", "mysql", "postgresql", "sqlite", "terraform",
}

# Tags that mark a model/dataset as being about source code.
CODE_TAGS = {
    "code", "coding", "programming", "programming-language", "programming-languages",
    "code-generation", "text-to-code", "code-completion", "codegen", "code-llm",
    "program-synthesis", "source-code", "code-search", "code-review", "code-translation",
    "code-summarization", "code-understanding", "code-instruct", "coder", "starcoder",
    "codellama", "code-llama", "codet5", "codebert", "software-engineering",
    "programming-language-modeling", "fill-in-the-middle", "fim", "automatic-programming",
    "text2code", "nl2code", "code-to-text", "code-model", "codeqwen", "qwen2.5-coder",
    "deepseek-coder", "competitive-programming", "humaneval", "mbpp", "bigcode",
}
