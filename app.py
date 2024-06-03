from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from plagiarism_detection import compare_code_fragments, extract_code_from_notebook_content
from minio_client import get_file_from_minio
from models import SQLDocumentVersion, SQLCodeFragment, SQLReport
import uuid
import logging

app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)
# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/sit-service-cheating-code', methods=['POST'])
def check_plagiarism():
    try:
        data = request.json
        doc_version_id = data['doc_version_id']
        
        # Получить файл из MinIO
        file_content = get_file_from_minio(doc_version_id)
        if not file_content:
            return jsonify({'error': 'File not found'}), 404

        # Извлечь фрагменты кода
        code_fragments = extract_code_from_notebook_content(file_content)

        # Сохранить фрагменты кода текущего документа в БД
        fragments_db = []
        for i, fragment in enumerate(code_fragments):
            code_fragment = SQLCodeFragment(
                id=uuid.uuid4(),
                document_version_id=doc_version_id,
                fragment=fragment,
                cell_number=i
            )
            db.session.add(code_fragment)
            fragments_db.append(code_fragment)
        db.session.commit()

        # Найти контрольную точку текущего документа
        doc_version = SQLDocumentVersion.query.get(doc_version_id)
        checkpoint_id = doc_version.document.report.checkpoint_id

        # Найти все другие версии документов для той же контрольной точки
        related_doc_versions = SQLDocumentVersion.query.join(SQLDocumentVersion.document) \
                                                       .join(SQLReport) \
                                                       .filter(SQLReport.checkpoint_id == checkpoint_id,
                                                               SQLDocumentVersion.id != doc_version_id).all()

        # Сравнить фрагменты кода текущего документа с другими версиями документов
        results = []
        for related_version in related_doc_versions:
            # Проверяем наличие фрагментов кода у текущей версии документа
            related_fragments = SQLCodeFragment.query.filter_by(document_version_id=related_version.id).all()
            
            # Если фрагментов кода нет, создаем их и сохраняем в БД
            if not related_fragments:
                # Получить файл из MinIO для текущей версии
                related_file_content = get_file_from_minio(related_version.id)
                if not related_file_content:
                    return jsonify({'error': 'File not found'}), 404
                
                # Извлечь фрагменты кода из файла
                related_code_fragments = extract_code_from_notebook_content(related_file_content)

                # Сохранить фрагменты кода в БД
                for j, related_fragment in enumerate(related_code_fragments):
                    related_code_fragment = SQLCodeFragment(
                        id=uuid.uuid4(),
                        document_version_id=related_version.id,
                        fragment=related_fragment,
                        cell_number=j
                    )
                    db.session.add(related_code_fragment)
                db.session.commit()

                # Обновляем список фрагментов кода для текущей версии документа
                related_fragments = SQLCodeFragment.query.filter_by(document_version_id=related_version.id).all()

            # Сравниваем фрагменты кода текущей версии с фрагментами кода текущего документа
            for fragment1 in fragments_db:
                for fragment2 in related_fragments:
                    similarity = compare_code_fragments(fragment1.fragment, fragment2.fragment)
                    if similarity > data.get('threshold', 0.5):
                        result = {
                            'cell_number': fragment1.cell_number,
                            'similarity': similarity,
                            'related_doc_version_id': related_version.id
                        }
                        results.append(result)

        return jsonify(results), 200

    except Exception as e:
        # Логирование ошибки
        logger.exception("An error occurred: %s", str(e))
        return jsonify({'error': 'An error occurred'}), 500



