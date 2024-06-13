import uuid
from difflib import SequenceMatcher
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
from starlette.responses import JSONResponse
from zss import Node, simple_distance
import nbformat
import re

from src.models.models import SQLCodeFragment, SQLDocumentVersion, SQLReport
from src.services.service_minio import get_file_from_minio


def tokenize_code(code, language):
    lexer = get_lexer_by_name(language)
    tokens = lexer.get_tokens(code)

    # Удаляем комментарии и пробелы
    tokens = [
        token[1].strip()
        for token in tokens
        if token[0] not in {Token.Comment.Single, Token.Comment.Multiline, Token.Text.Whitespace} and token[1].strip()
    ]

    # Убираем любые строковые литералы и числовые значения, заменяя их на специальные токены
    tokens = [
        re.sub(r'".*?"', 'STRING_LITERAL', token) for token in tokens
    ]
    tokens = [
        re.sub(r'\d+', 'NUMBER_LITERAL', token) for token in tokens
    ]

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
        if token == '(':
            stack[-1].addkid(node)
            stack.append(node)
        elif token == ')':
            if len(stack) > 1:
                stack.pop()
        else:
            stack[-1].addkid(node)

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

    print(f"LCS Similarity: {lcs_sim}")
    print(f"Damerau-Levenshtein Similarity: {damerau_levenshtein_sim}")
    print(f"ZSS Similarity: {zss_similarity}")

    return (damerau_levenshtein_sim + lcs_sim + zss_similarity) / 3


async def check_plagiarism(
    doc_version_id,
    language,
    threshold,
    async_session
):
    # Получить файл из Minio
    file_content = get_file_from_minio(doc_version_id)
    if not file_content:
        raise Exception("File not found")

    # Извлечь фрагменты кода
    code_fragments = extract_code_from_notebook_content(file_content)

    # Сохранить фрагменты кода текущего документа в БД
    fragments_db = []
    async with async_session.begin():
        for i, fragment in enumerate(code_fragments):
            code_fragment = SQLCodeFragment(
                id=uuid.uuid4(),
                document_version_id=doc_version_id,
                fragment=fragment,
                cell_number=i
            )
            async_session.add(code_fragment)
            fragments_db.append(code_fragment)
        await async_session.commit()

    # Найти контрольную точку текущего документа
    doc_version = await async_session.query(SQLDocumentVersion).get(doc_version_id)
    checkpoint_id = doc_version.document.report.checkpoint_id

    # Найти все другие версии документов для той же контрольной точки
    related_doc_versions = await async_session.query(SQLDocumentVersion).join(SQLDocumentVersion.document) \
        .join(SQLReport) \
        .filter(SQLReport.checkpoint_id == checkpoint_id,
                SQLDocumentVersion.id != doc_version_id).all()

    # Сравнить фрагменты кода текущего документа с другими версиями документов
    results = []
    for related_version in related_doc_versions:
        # Проверяем наличие фрагментов кода у текущей версии документа
        related_fragments = await async_session.query(SQLCodeFragment).filter_by(
            document_version_id=related_version.id).all()

        # Если фрагментов кода нет, создаем их и сохраняем в БД
        if not related_fragments:
            # Получить файл из Minio для текущей версии
            related_file_content = get_file_from_minio(related_version.id)
            if not related_file_content:
                raise Exception("File not found")

            # Извлечь фрагменты кода из файла
            related_code_fragments = extract_code_from_notebook_content(related_file_content)

            # Сохранить фрагменты кода в БД
            async with async_session.begin():
                for j, related_fragment in enumerate(related_code_fragments):
                    related_code_fragment = SQLCodeFragment(
                        id=uuid.uuid4(),
                        document_version_id=related_version.id,
                        fragment=related_fragment,
                        cell_number=j
                    )
                    async_session.add(related_code_fragment)
                await async_session.commit()

            # Обновляем список фрагментов кода для текущей версии документа
            related_fragments = async_session.query(SQLCodeFragment).filter_by(
                document_version_id=related_version.id).all()

        # Сравниваем фрагменты кода текущей версии с фрагментами кода текущего документа
        for fragment1 in fragments_db:
            for fragment2 in related_fragments:
                similarity = compare_code_fragments(
                    fragment1.fragment,
                    fragment2.fragment,
                    language
                )
                if similarity > threshold:
                    result = {
                        'cell_number': fragment1.cell_number,
                        'similarity': similarity,
                        'related_doc_version_id': related_version.id
                    }
                    results.append(result)

    return JSONResponse(content=results)


