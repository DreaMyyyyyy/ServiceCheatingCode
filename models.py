from sqlalchemy import Column, String, Text, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, DeclarativeBase
import uuid

# Базовый класс для всех моделей
class Base(DeclarativeBase):
    pass
    
# Модель пользователя
class SQLUser(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# Модель студента, который также является пользователем
class SQLStudent(Base):
    __tablename__ = 'students'
    id = Column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    group = Column(String)
    user = relationship("SQLUser", back_populates="student")

# Модель предмета
class SQLSubject(Base):
    __tablename__ = 'subjects'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)

# Модель контрольной точки
class SQLCheckpoint(Base):
    __tablename__ = 'checkpoints'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.id'))
    subject = relationship("SQLSubject")
    reports = relationship("SQLReport", back_populates="checkpoint")

# Модель отчета
class SQLReport(Base):
    __tablename__ = 'reports'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'))
    checkpoint_id = Column(UUID(as_uuid=True), ForeignKey('checkpoints.id'))
    student = relationship("SQLStudent", back_populates="reports")
    checkpoint = relationship("SQLCheckpoint", back_populates="reports")
    documents = relationship("SQLDocument", back_populates="report")

# Модель документа
class SQLDocument(Base):
    __tablename__ = 'documents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey('reports.id'))
    report = relationship("SQLReport", back_populates="documents")
    versions = relationship("SQLDocumentVersion", back_populates="document")

# Модель версии документа
class SQLDocumentVersion(Base):
    __tablename__ = 'document_versions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'))
    version = Column(Integer, nullable=False)
    dttm = Column(TIMESTAMP, nullable=False)
    document = relationship("SQLDocument", back_populates="versions")
    code_fragments = relationship("SQLCodeFragment", back_populates="document_version")

# Модель фрагмента кода
class SQLCodeFragment(Base):
    __tablename__ = 'code_fragments'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey('document_versions.id'))
    fragment = Column(Text, nullable=False)
    cell_number = Column(Integer, nullable=False)
    document_version = relationship("SQLDocumentVersion", back_populates="code_fragments")

# Связь User с Teacher и Student
SQLUser.student = relationship("SQLStudent", uselist=False, back_populates="user")

# Связь Student с Report
SQLStudent.reports = relationship("SQLReport", back_populates="student")

# Связь Checkpoint с Report
SQLCheckpoint.reports = relationship("SQLReport", back_populates="checkpoint")

# Связь Report с Document
SQLReport.documents = relationship("SQLDocument", back_populates="report")

# Связь Document с DocumentVersion
SQLDocument.versions = relationship("SQLDocumentVersion", back_populates="document")

# Связь DocumentVersion с CodeFragment
SQLDocumentVersion.code_fragments = relationship("SQLCodeFragment", back_populates="document_version")

