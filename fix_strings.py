import pathlib
import re

for path in pathlib.Path("nonkyc").rglob("*.py"):
    text = path.read_text()

    # фикс: console.print(Panel("  → закрываем строку
    text = re.sub(
        r'console\.print\(Panel\("(\s*)$',
        r'console.print(Panel(""))',
        text,
        flags=re.MULTILINE
    )

    # фикс оборванных f-string
    text = re.sub(
        r'f"([^"\n]*)$',
        r'f"\1"',
        text,
        flags=re.MULTILINE
    )

    path.write_text(text)

print("Done fixing strings")
