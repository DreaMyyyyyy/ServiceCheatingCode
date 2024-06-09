from difflib import SequenceMatcher
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from zss import Node, simple_distance
import nbformat

def tokenize_code(code, language):
    lexer = get_lexer_by_name(language)
    tokens = lexer.get_tokens(code)
    # Удаляем комментарии и пустые строки
    tokens = [token[1].strip() for token in tokens if token[0] not in {Token.Comment.Single, Token.Comment.Multiline, Token.Text.Whitespace} and token[1].strip()]
    return tokens

def extract_code_from_notebook_content(notebook_content):
    code_fragments = []
    try:
        notebook = nbformat.reads(notebook_content, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                code_fragments.append(cell.source)
    except nbformat.reader.NotJSONError:
        print("Error: Not a valid JSON format for the notebook content.")
        pass
    return code_fragments

def damerau_levenshtein_distance(seq1, seq2):
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if seq1[i - 1] == seq2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1,  # удаление
                           dp[i][j - 1] + 1,  # вставка
                           dp[i - 1][j - 1] + cost)  # замена
            if i > 1 and j > 1 and seq1[i - 1] == seq2[j - 2] and seq1[i - 2] == seq2[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + cost)  # транспозиция

    return dp[m][n]

def damerau_levenshtein_similarity(seq1, seq2):
    distance = damerau_levenshtein_distance(seq1, seq2)
    max_len = max(len(seq1), len(seq2))
    return 1 - distance / max_len

def zhang_shasha_distance(tokens1, tokens2):
    tree1 = convert_to_zss(tokens1)
    tree2 = convert_to_zss(tokens2)
    return simple_distance(tree1, tree2)

def convert_to_zss(tokens):
    if not tokens:
        return Node("empty")

    root = Node("root")
    stack = [root]

    for token in tokens:
        node = Node(token)
        stack[-1].addkid(node)
        if token == '(':
            stack.append(node)
        elif token == ')':
            if len(stack) > 1:
                stack.pop()

    return root

def compare_code_fragments(code1, code2, language):
    tokens1 = tokenize_code(code1, language)
    tokens2 = tokenize_code(code2, language)

    damerau_levenshtein_sim = damerau_levenshtein_similarity(tokens1, tokens2)
    seq_matcher = SequenceMatcher(None, tokens1, tokens2)
    lcs_sim = seq_matcher.ratio()

    zss_distance = zhang_shasha_distance(tokens1, tokens2)
    max_len = max(len(tokens1), len(tokens2))
    zss_similarity = 1 - zss_distance / max_len

    print(lcs_sim)
    print('\n')
    print(damerau_levenshtein_sim)
    print('\n')
    print(zss_similarity)
    print('\n')
    
    return (damerau_levenshtein_sim + lcs_sim + zss_similarity) / 3











