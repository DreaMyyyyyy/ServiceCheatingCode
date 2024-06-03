from difflib import SequenceMatcher
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from zss import Node
import nbformat

def tokenize_code(code, language):
    lexer = get_lexer_by_name(language)
    tokens = lexer.get_tokens(code)
    # Удаляем префиксные пробелы из токенов
    tokens = [token[1].lstrip() for token in tokens if token[0] != Token.Comment]
    return tokens

def extract_code_from_notebook_content(notebook_content):
    code_fragments = []
    try:
        notebook = nbformat.reads(notebook_content, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                code_fragments.append(cell.source)
    except nbformat.reader.NotJSONError:
        # В случае неверного формата блокнота
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

def convert_to_zss(tokens):
    root = Node("root")
    stack = [root]

    for token in tokens:
        node = Node(token)
        stack[-1].addkid(node)
        if token == '(':
            stack.append(node)
        elif token == ')':
            stack.pop()

    return root

def count_nodes(tree):
    if tree is None:
        return 0
    count = 1
    for child in tree.children:
        count += count_nodes(child)
    return count

def count_matching_nodes(tree1, tree2):
    if tree1 is None or tree2 is None:
        return 0
    matching_count = 0
    if tree1.label == tree2.label:
        matching_count += 1
    for child1, child2 in zip(tree1.children, tree2.children):
        matching_count += count_matching_nodes(child1, child2)
    return matching_count

def zhang_shasha_distance(tokens1, tokens2):
    tree1 = convert_to_zss(tokens1)
    tree2 = convert_to_zss(tokens2)

    print("Tree1:")
    print_tree(tree1)
    print("\nTree2:")
    print_tree(tree2)

    nodes1_count = count_nodes(tree1)
    nodes2_count = count_nodes(tree2)

    matching_nodes_count = count_matching_nodes(tree1, tree2)

    total_nodes = nodes1_count + nodes2_count - matching_nodes_count

    if total_nodes == 0:
        return 1.0
    else:
        similarity = matching_nodes_count / total_nodes

    return similarity

def print_tree(node, level=0):
    print("  " * level + str(node.label))
    for child in node.children:
        print_tree(child, level + 1)

def compare_code_fragments(code1, code2, language):
    tokens1 = tokenize_code(code1, language)
    tokens2 = tokenize_code(code2, language)

    print(f"Tokens1 ({language}):", tokens1)
    print(f"Tokens2 ({language}):", tokens2)

    damerau_levenshtein_sim = damerau_levenshtein_similarity(tokens1, tokens2)
    seq_matcher = SequenceMatcher(None, tokens1, tokens2)
    lcs_sim = seq_matcher.ratio()

    zss_similarity = zhang_shasha_distance(tokens1, tokens2)

    print("AST Similarity:", zss_similarity)
    print("damerau_levenshtein_sim:", damerau_levenshtein_sim)
    print("lcs_sim:", lcs_sim)

    return (damerau_levenshtein_sim + lcs_sim) / 2











