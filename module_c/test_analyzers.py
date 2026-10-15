from module_c.analyzers_c import analyze_code

test_code = """
#include <string.h>

void copy_input(const char *input) {
    char buffer[8];
    strcpy(buffer, input);
}
"""


results = analyze_code(test_code, language="c")


for tool, result in results.items():
    print(f"\n--- {tool.upper()} ---")
    print(f"Success: {result['success']}")
    print(result["findings"])

