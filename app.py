from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi_sqlalchemy import DBSessionMiddleware, db
from plagiarism_detection import compare_code_fragments, extract_code_from_notebook_content
from minio_client import get_file_from_minio
from models import SQLDocumentVersion, SQLCodeFragment, SQLReport
import uuid
import logging
import os

app = FastAPI()

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка подключения к БД и Minio
app.add_middleware(DBSessionMiddleware, db_url=os.getenv('DATABASE_URL'))

@app.post('/sit-service-cheating-code')
async def check_plagiarism(request: Request):
    try:
        data = await request.json()
        doc_version_id = data['doc_version_id']
        
        # Получить файл из Minio
        file_content = get_file_from_minio(doc_version_id)
        if not file_content:
            raise HTTPException(status_code=404, detail="File not found")

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
        doc_version = db.session.query(SQLDocumentVersion).get(doc_version_id)
        checkpoint_id = doc_version.document.report.checkpoint_id

        # Найти все другие версии документов для той же контрольной точки
        related_doc_versions = db.session.query(SQLDocumentVersion).join(SQLDocumentVersion.document) \
                                                       .join(SQLReport) \
                                                       .filter(SQLReport.checkpoint_id == checkpoint_id,
                                                               SQLDocumentVersion.id != doc_version_id).all()

        # Сравнить фрагменты кода текущего документа с другими версиями документов
        results = []
        for related_version in related_doc_versions:
            # Проверяем наличие фрагментов кода у текущей версии документа
            related_fragments = db.session.query(SQLCodeFragment).filter_by(document_version_id=related_version.id).all()
            
            # Если фрагментов кода нет, создаем их и сохраняем в БД
            if not related_fragments:
                # Получить файл из Minio для текущей версии
                related_file_content = get_file_from_minio(related_version.id)
                if not related_file_content:
                    raise HTTPException(status_code=404, detail="File not found")
                
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
                related_fragments = db.session.query(SQLCodeFragment).filter_by(document_version_id=related_version.id).all()

            # Сравниваем фрагменты кода текущей версии с фрагментами кода текущего документа
            for fragment1 in fragments_db:
                for fragment2 in related_fragments:
                    similarity = compare_code_fragments(fragment1.fragment, fragment2.fragment, data.get('language', 'python'))
                    if similarity > data.get('threshold', 0.5):
                        result = {
                            'cell_number': fragment1.cell_number,
                            'similarity': similarity,
                            'related_doc_version_id': related_version.id
                        }
                        results.append(result)

        return JSONResponse(content=results)

    except Exception as e:
        # Логирование ошибки
        logger.exception("An error occurred: %s", str(e))
        raise HTTPException(status_code=500, detail="An error occurred")




