from flask import Blueprint, request, jsonify
import sqlite3
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

database_manager_bp = Blueprint('database_manager', __name__)

class DatabaseManager:
    def __init__(self, base_path: str = "/home/ubuntu/sebaircode-databases"):
        self.base_path = base_path
        self.ensure_base_directory()
    
    def ensure_base_directory(self):
        """Ensure the base directory for databases exists"""
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)
    
    def create_database(self, app_id: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new database for an application"""
        try:
            db_path = os.path.join(self.base_path, f"{app_id}.db")
            
            # Create database connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create tables based on schema
            for table_name, table_config in schema.get('tables', {}).items():
                self._create_table(cursor, table_name, table_config)
            
            # Insert sample data if provided
            for table_name, table_config in schema.get('tables', {}).items():
                if 'sample_data' in table_config:
                    self._insert_sample_data(cursor, table_name, table_config['sample_data'])
            
            conn.commit()
            conn.close()
            
            # Save database metadata
            metadata = {
                'app_id': app_id,
                'db_path': db_path,
                'schema': schema,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self._save_metadata(app_id, metadata)
            
            return {
                'success': True,
                'database_id': app_id,
                'connection_string': f"sqlite:///{db_path}",
                'tables': list(schema.get('tables', {}).keys()),
                'metadata': metadata
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_table(self, cursor: sqlite3.Cursor, table_name: str, table_config: Dict[str, Any]):
        """Create a table based on configuration"""
        columns = []
        
        for column_name, column_config in table_config.get('columns', {}).items():
            column_def = f"{column_name} {column_config.get('type', 'TEXT')}"
            
            if column_config.get('primary_key'):
                column_def += " PRIMARY KEY"
            
            if column_config.get('auto_increment'):
                column_def += " AUTOINCREMENT"
            
            if column_config.get('not_null'):
                column_def += " NOT NULL"
            
            if 'default' in column_config:
                column_def += f" DEFAULT {column_config['default']}"
            
            columns.append(column_def)
        
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        cursor.execute(create_sql)
        
        # Create indexes if specified
        for index_config in table_config.get('indexes', []):
            index_name = f"idx_{table_name}_{index_config['column']}"
            index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({index_config['column']})"
            cursor.execute(index_sql)
    
    def _insert_sample_data(self, cursor: sqlite3.Cursor, table_name: str, sample_data: List[Dict[str, Any]]):
        """Insert sample data into a table"""
        if not sample_data:
            return
        
        for row in sample_data:
            columns = list(row.keys())
            placeholders = ', '.join(['?' for _ in columns])
            values = list(row.values())
            
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(insert_sql, values)
    
    def _save_metadata(self, app_id: str, metadata: Dict[str, Any]):
        """Save database metadata"""
        metadata_path = os.path.join(self.base_path, f"{app_id}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def get_database_info(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Get database information"""
        try:
            metadata_path = os.path.join(self.base_path, f"{app_id}_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception:
            return None
    
    def execute_query(self, app_id: str, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute a query on the database"""
        try:
            db_info = self.get_database_info(app_id)
            if not db_info:
                return {'success': False, 'error': 'Database not found'}
            
            db_path = db_info['db_path']
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = [dict(row) for row in cursor.fetchall()]
                return {
                    'success': True,
                    'data': results,
                    'row_count': len(results)
                }
            else:
                conn.commit()
                return {
                    'success': True,
                    'affected_rows': cursor.rowcount
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def backup_database(self, app_id: str) -> Dict[str, Any]:
        """Create a backup of the database"""
        try:
            db_info = self.get_database_info(app_id)
            if not db_info:
                return {'success': False, 'error': 'Database not found'}
            
            db_path = db_info['db_path']
            backup_filename = f"{app_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = os.path.join(self.base_path, 'backups', backup_filename)
            
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy database file
            import shutil
            shutil.copy2(db_path, backup_path)
            
            return {
                'success': True,
                'backup_path': backup_path,
                'backup_filename': backup_filename,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """List all databases"""
        databases = []
        
        try:
            for filename in os.listdir(self.base_path):
                if filename.endswith('_metadata.json'):
                    app_id = filename.replace('_metadata.json', '')
                    db_info = self.get_database_info(app_id)
                    if db_info:
                        databases.append(db_info)
        except Exception:
            pass
        
        return databases

class SchemaGenerator:
    """Generate database schemas based on app requirements"""
    
    @staticmethod
    def generate_schema_for_app_type(app_type: str, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate database schema based on application type"""
        
        if app_type == 'restaurant_website':
            return SchemaGenerator._restaurant_schema(app_config)
        elif app_type == 'ecommerce':
            return SchemaGenerator._ecommerce_schema(app_config)
        elif app_type == 'blog':
            return SchemaGenerator._blog_schema(app_config)
        elif app_type == 'portfolio':
            return SchemaGenerator._portfolio_schema(app_config)
        else:
            return SchemaGenerator._basic_schema(app_config)
    
    @staticmethod
    def _restaurant_schema(app_config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'tables': {
                'menu_categories': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'name': {'type': 'TEXT', 'not_null': True},
                        'description': {'type': 'TEXT'},
                        'display_order': {'type': 'INTEGER', 'default': 0},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    },
                    'sample_data': [
                        {'name': 'المقبلات', 'description': 'مقبلات شهية ومتنوعة', 'display_order': 1},
                        {'name': 'الأطباق الرئيسية', 'description': 'أطباق رئيسية لذيذة', 'display_order': 2},
                        {'name': 'الحلويات', 'description': 'حلويات شرقية وغربية', 'display_order': 3}
                    ]
                },
                'menu_items': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'category_id': {'type': 'INTEGER', 'not_null': True},
                        'name': {'type': 'TEXT', 'not_null': True},
                        'description': {'type': 'TEXT'},
                        'price': {'type': 'DECIMAL(10,2)', 'not_null': True},
                        'image_url': {'type': 'TEXT'},
                        'is_available': {'type': 'BOOLEAN', 'default': 1},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    },
                    'indexes': [
                        {'column': 'category_id'},
                        {'column': 'is_available'}
                    ],
                    'sample_data': [
                        {'category_id': 1, 'name': 'حمص بالطحينة', 'description': 'حمص طازج مع الطحينة والزيت', 'price': 15.00},
                        {'category_id': 1, 'name': 'متبل', 'description': 'متبل باذنجان مشوي', 'price': 12.00},
                        {'category_id': 2, 'name': 'كباب لحم', 'description': 'كباب لحم مشوي مع الأرز', 'price': 45.00},
                        {'category_id': 3, 'name': 'كنافة نابلسية', 'description': 'كنافة طازجة بالجبن', 'price': 20.00}
                    ]
                },
                'reservations': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'customer_name': {'type': 'TEXT', 'not_null': True},
                        'customer_phone': {'type': 'TEXT', 'not_null': True},
                        'customer_email': {'type': 'TEXT'},
                        'reservation_date': {'type': 'DATE', 'not_null': True},
                        'reservation_time': {'type': 'TIME', 'not_null': True},
                        'party_size': {'type': 'INTEGER', 'not_null': True},
                        'special_requests': {'type': 'TEXT'},
                        'status': {'type': 'TEXT', 'default': "'pending'"},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    },
                    'indexes': [
                        {'column': 'reservation_date'},
                        {'column': 'status'}
                    ]
                }
            }
        }
    
    @staticmethod
    def _ecommerce_schema(app_config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'tables': {
                'categories': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'name': {'type': 'TEXT', 'not_null': True},
                        'description': {'type': 'TEXT'},
                        'parent_id': {'type': 'INTEGER'},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    }
                },
                'products': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'name': {'type': 'TEXT', 'not_null': True},
                        'description': {'type': 'TEXT'},
                        'price': {'type': 'DECIMAL(10,2)', 'not_null': True},
                        'category_id': {'type': 'INTEGER'},
                        'stock_quantity': {'type': 'INTEGER', 'default': 0},
                        'image_url': {'type': 'TEXT'},
                        'is_active': {'type': 'BOOLEAN', 'default': 1},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    },
                    'indexes': [
                        {'column': 'category_id'},
                        {'column': 'is_active'}
                    ]
                },
                'orders': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'customer_name': {'type': 'TEXT', 'not_null': True},
                        'customer_email': {'type': 'TEXT', 'not_null': True},
                        'customer_phone': {'type': 'TEXT'},
                        'total_amount': {'type': 'DECIMAL(10,2)', 'not_null': True},
                        'status': {'type': 'TEXT', 'default': "'pending'"},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    }
                }
            }
        }
    
    @staticmethod
    def _blog_schema(app_config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'tables': {
                'posts': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'title': {'type': 'TEXT', 'not_null': True},
                        'content': {'type': 'TEXT', 'not_null': True},
                        'excerpt': {'type': 'TEXT'},
                        'author': {'type': 'TEXT', 'not_null': True},
                        'featured_image': {'type': 'TEXT'},
                        'is_published': {'type': 'BOOLEAN', 'default': 0},
                        'published_at': {'type': 'DATETIME'},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    },
                    'indexes': [
                        {'column': 'is_published'},
                        {'column': 'published_at'}
                    ]
                },
                'comments': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'post_id': {'type': 'INTEGER', 'not_null': True},
                        'author_name': {'type': 'TEXT', 'not_null': True},
                        'author_email': {'type': 'TEXT', 'not_null': True},
                        'content': {'type': 'TEXT', 'not_null': True},
                        'is_approved': {'type': 'BOOLEAN', 'default': 0},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    },
                    'indexes': [
                        {'column': 'post_id'},
                        {'column': 'is_approved'}
                    ]
                }
            }
        }
    
    @staticmethod
    def _portfolio_schema(app_config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'tables': {
                'projects': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'title': {'type': 'TEXT', 'not_null': True},
                        'description': {'type': 'TEXT'},
                        'technologies': {'type': 'TEXT'},
                        'project_url': {'type': 'TEXT'},
                        'github_url': {'type': 'TEXT'},
                        'image_url': {'type': 'TEXT'},
                        'display_order': {'type': 'INTEGER', 'default': 0},
                        'is_featured': {'type': 'BOOLEAN', 'default': 0},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    }
                },
                'skills': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'name': {'type': 'TEXT', 'not_null': True},
                        'category': {'type': 'TEXT'},
                        'proficiency_level': {'type': 'INTEGER', 'default': 1},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    }
                }
            }
        }
    
    @staticmethod
    def _basic_schema(app_config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'tables': {
                'content': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'title': {'type': 'TEXT', 'not_null': True},
                        'content': {'type': 'TEXT'},
                        'type': {'type': 'TEXT', 'default': "'page'"},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    }
                },
                'contacts': {
                    'columns': {
                        'id': {'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
                        'name': {'type': 'TEXT', 'not_null': True},
                        'email': {'type': 'TEXT', 'not_null': True},
                        'message': {'type': 'TEXT', 'not_null': True},
                        'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'}
                    }
                }
            }
        }

# Initialize the database manager
db_manager = DatabaseManager()
schema_generator = SchemaGenerator()

@database_manager_bp.route('/create', methods=['POST'])
def create_database():
    """Create a new database for an application"""
    try:
        data = request.get_json()
        app_id = data.get('app_id') or str(uuid.uuid4())
        app_type = data.get('app_type', 'basic')
        app_config = data.get('app_config', {})
        
        # Generate schema based on app type
        schema = schema_generator.generate_schema_for_app_type(app_type, app_config)
        
        # Create database
        result = db_manager.create_database(app_id, schema)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@database_manager_bp.route('/info/<app_id>', methods=['GET'])
def get_database_info(app_id):
    """Get database information"""
    try:
        db_info = db_manager.get_database_info(app_id)
        
        if db_info:
            return jsonify({'success': True, 'data': db_info})
        else:
            return jsonify({'success': False, 'error': 'Database not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@database_manager_bp.route('/query/<app_id>', methods=['POST'])
def execute_query(app_id):
    """Execute a query on the database"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        params = data.get('params', [])
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        result = db_manager.execute_query(app_id, query, params)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@database_manager_bp.route('/backup/<app_id>', methods=['POST'])
def backup_database(app_id):
    """Create a backup of the database"""
    try:
        result = db_manager.backup_database(app_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@database_manager_bp.route('/list', methods=['GET'])
def list_databases():
    """List all databases"""
    try:
        databases = db_manager.list_databases()
        return jsonify({'success': True, 'data': databases})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@database_manager_bp.route('/schemas', methods=['GET'])
def get_available_schemas():
    """Get available database schemas"""
    schemas = {
        'restaurant_website': {
            'name': 'موقع مطعم',
            'description': 'قاعدة بيانات لموقع مطعم مع قوائم الطعام والحجوزات',
            'tables': ['menu_categories', 'menu_items', 'reservations']
        },
        'ecommerce': {
            'name': 'متجر إلكتروني',
            'description': 'قاعدة بيانات لمتجر إلكتروني مع المنتجات والطلبات',
            'tables': ['categories', 'products', 'orders']
        },
        'blog': {
            'name': 'مدونة',
            'description': 'قاعدة بيانات لمدونة مع المقالات والتعليقات',
            'tables': ['posts', 'comments']
        },
        'portfolio': {
            'name': 'معرض أعمال',
            'description': 'قاعدة بيانات لمعرض الأعمال مع المشاريع والمهارات',
            'tables': ['projects', 'skills']
        },
        'basic': {
            'name': 'أساسي',
            'description': 'قاعدة بيانات أساسية للمحتوى والاتصالات',
            'tables': ['content', 'contacts']
        }
    }
    
    return jsonify({'success': True, 'data': schemas})

