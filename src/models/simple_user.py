#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelo simplificado para usuários
Sistema Federal Associados - Versão Simplificada
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict
import os
import hashlib

class SimpleUser:
    """Modelo simplificado para usuários"""
    
    def __init__(self, id=None, email=None, password_hash=None, name=None, 
                 role='client', created_at=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.name = name
        self.role = role  # 'client' ou 'admin'
        self.created_at = created_at or datetime.now().isoformat()
    
    @staticmethod
    def get_db_connection():
        """Conectar ao banco de dados"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'federal_system.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    @classmethod
    def get_by_email(cls, email: str) -> Optional['SimpleUser']:
        """Obter usuário por email"""
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, password_hash, name, role, created_at
            FROM users 
            WHERE email = ?
        """, (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row['id'],
                email=row['email'],
                password_hash=row['password_hash'],
                name=row['name'],
                role=row['role'],
                created_at=row['created_at']
            )
        return None
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['SimpleUser']:
        """Obter usuário por ID"""
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, password_hash, name, role, created_at
            FROM users 
            WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls(
                id=row['id'],
                email=row['email'],
                password_hash=row['password_hash'],
                name=row['name'],
                role=row['role'],
                created_at=row['created_at']
            )
        return None
    
    @classmethod
    def create_user(cls, email: str, password: str, name: str, role: str = 'client') -> Optional['SimpleUser']:
        """Criar novo usuário"""
        # Hash da senha
        password_hash = cls.hash_password(password)
        
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (email, password_hash, name, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (email, password_hash, name, role, datetime.now().isoformat()))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return cls(
                id=user_id,
                email=email,
                password_hash=password_hash,
                name=name,
                role=role,
                created_at=datetime.now().isoformat()
            )
            
        except sqlite3.IntegrityError:
            conn.close()
            return None  # Email já existe
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Erro ao criar usuário: {e}")
            return None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash da senha usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verificar senha"""
        return self.password_hash == self.hash_password(password)
    
    def is_admin(self) -> bool:
        """Verificar se é administrador"""
        return self.role == 'admin'
    
    def to_dict(self, include_password=False) -> Dict:
        """Converter para dicionário"""
        result = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at
        }
        
        if include_password:
            result['password_hash'] = self.password_hash
            
        return result
    
    def save(self) -> bool:
        """Salvar usuário no banco de dados"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            if self.id:
                # Atualizar usuário existente
                cursor.execute("""
                    UPDATE users 
                    SET email = ?, password_hash = ?, name = ?, role = ?
                    WHERE id = ?
                """, (self.email, self.password_hash, self.name, self.role, self.id))
            else:
                # Criar novo usuário
                cursor.execute("""
                    INSERT INTO users (email, password_hash, name, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.email, self.password_hash, self.name, self.role, self.created_at))
                self.id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Erro ao salvar usuário: {e}")
            return False