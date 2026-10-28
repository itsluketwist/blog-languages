"""Shared paths, pinned data sources and hand-curated lists for the analysis."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIGURES = ROOT / "figures"

# the quarter of github innovation graph data that the analysis uses
PERIOD = (2026, 1)

# both sources are pinned to a fixed commit, so re-running reads the exact same files
INNOVATION_GRAPH_URL = (
    "https://raw.githubusercontent.com/github/innovationgraph/"
    "db6ccdf6a8938e10a4304447e3e302562fda3e64/data/languages.csv"
)
LINGUIST_URL = (
    "https://raw.githubusercontent.com/github-linguist/linguist/"
    "73ee9a3b277f398c37ca4ab0dea0193849de6460/lib/linguist/languages.yml"
)

# linguist calls these "programming" languages, but they are build/config/installer
# formats rather than languages people would want a model for.
EXCLUDED = {
    "Dockerfile",
    "Makefile",
    "CMake",
    "Procfile",
    "Meson",
    "QMake",
    "M4",
    "M4Sugar",
    "Inno Setup",
    "NSIS",
    "BitBake",
    "GDB",
    "Module Management System",
    "Filebench WML",
    "Earthly",
    "Singularity",
    "RPC",
    "Linker Script",
    # hack shares the .php extension with php, so linguist credits it with
    # implausibly many developers (~112k across 96 economies).
    "Hack",
}

# sql dialects are folded into a single "SQL" entry, because on hugging face
# almost everything sql-related is tagged generically ("sql", "mysql", ...).
SQL_DIALECTS = {"SQL", "PLpgSQL", "TSQL", "PLSQL", "SQLPL", "HiveQL"}

# the "dead languages" of programming: old languages with few active github
# developers today, the analogue of latin / ancient greek in the talk.
LEGACY = {
    "COBOL",
    "Fortran",
    "Pascal",
    "Ada",
    "Smalltalk",
    "BASIC",
    "Visual Basic 6.0",
    "Modula-2",
    "Modula-3",
    "REXX",
    "RPGLE",
    "Forth",
    "Classic ASP",
    "ActionScript",
    "Eiffel",
    "ABAP",
    "Common Lisp",
    "Prolog",
    "VBA",
    "CoffeeScript",
}

# extra hugging face tags per language, on top of the name and linguist aliases.
# these are only other spellings or versions of the language's own name; task tags
# (e.g. "text-to-sql") are deliberately left out, because only some languages
# have them and including them would favour those languages.
EXTRA_TAGS = {
    "SQL": ["sql", "t-sql", "pl-sql", "mysql", "postgresql", "sqlite"],
    "Go": ["golang"],
    "C#": ["c-sharp", "csharp"],
    "C++": ["cpp", "cplusplus"],
    "JavaScript": ["javascript", "js", "nodejs"],
    "Shell": ["bash", "shell-script"],
    "Lean": ["lean4", "lean-4", "lean3"],
    "Assembly": ["asm", "assembly-code"],
    "R": ["rstats", "r-language"],
    "C": ["c-language"],
}

# tags that collide with ordinary words, natural-language codes, or are simply too
# short to mean "this programming language" on their own. a model/dataset only
# counts for these when it is also tagged as being about code (see CODE_TAGS) or
# with another, unambiguous programming-language tag.
AMBIGUOUS = {
    "hack", "mako", "red", "io", "e", "j", "m", "q", "v", "d", "r", "c", "cool", "clean",
    "slash", "max", "logos", "limbo", "arc", "turing", "ink", "berry", "pike", "fluent",
    "move", "stan", "euphoria", "cadence", "sage", "faust", "alloy", "squirrel",
    "papyrus", "nasal", "janet", "elvish", "jasmin", "boogie", "puppet", "mercury",
    "dm", "txl", "terra", "idl", "flux", "zap", "nu", "ecl", "al", "eiffel", "clarity",
    "processing", "assembly", "julia", "dart", "swift", "ruby", "rust", "go", "lean",
    "reason", "crystal", "elm", "gleam", "odin", "vala", "zig", "agda", "gap",
    "fennel", "pawn", "metal", "smali", "yacc", "lex", "sed", "awk", "node", "emacs",
    "cake", "cakescript", "max/msp", "nim", "ada", "lua", "sh", "ts", "pl", "hy", "ml",
    "as", "bash", "asm", "cpp", "lisp", "scheme",
    "prolog", "basic", "forth", "pascal", "apex", "motoko", "ballerina", "haxe", "csound",
    "chuck", "lasso", "rexx", "dafny", "idris", "bluespec", "pony", "racket", "cue",
    "nix", "stata", "sas", "mathematica", "matlab", "ampl", "gams", "modelica", "lilypond",
    "supercollider", "jq", "llvm", "mlir", "webassembly", "wasm", "cuda", "inc", "rake",
    "posh", "bat", "batch", "envrc", "mysql", "postgresql", "sqlite", "terraform",
    "delphi", "sieve", "flex", "coffee", "smpl", "mumps", "renpy",
}  # fmt: skip

# linguist aliases that on the hub almost always mean something else (apple's m2
# chip and mps backend, ...). these are never used as tags for the language.
DROPPED_TAGS = {"m2", "mps", "dcl", "al", "be", "inc"}

# languages whose names mostly mean something else on the hub (gpu runtimes, a
# quantisation method, a benchmark, ...), even on code models, so tag counts can't
# measure them. they are left out of the analysis rather than reported as zero.
UNMEASURABLE = {
    "Cuda", "Metal", "WebAssembly", "Apex", "Arc", "Reason", "Hy", "Io", "Max", "Limbo",
    "Berry", "Fluent", "Move", "Turing", "Ink", "Cool", "Clean", "Slash", "Logos", "E",
    "Red", "V", "J", "M", "q", "Sage", "Stan", "Alloy", "Cadence", "Euphoria", "Faust",
    "FLUX", "AL",
}  # fmt: skip

# tags that mark a model/dataset as being about source code. datasets declare
# "code" as their language, which the hub turns into the tag "language:code".
CODE_TAGS = {
    "code", "language:code", "coding", "programming", "programming-language",
    "programming-languages", "code-generation", "text-to-code", "code-completion",
    "codegen", "code-llm", "program-synthesis", "source-code", "code-search",
    "code-review", "code-translation", "code-summarization", "code-understanding",
    "code-instruct", "coder", "starcoder", "codellama", "code-llama", "codet5",
    "codebert", "software-engineering", "programming-language-modeling",
    "fill-in-the-middle", "fim", "automatic-programming", "text2code", "nl2code",
    "code-to-text", "code-model", "codeqwen", "qwen2.5-coder", "deepseek-coder",
    "competitive-programming", "humaneval", "mbpp", "bigcode",
}  # fmt: skip

# a repo tagged with more programming languages than this is treated as a general
# code model in the "dedicated" sensitivity count (the main count keeps it).
DEDICATED_MAX_LANGUAGES = 3
