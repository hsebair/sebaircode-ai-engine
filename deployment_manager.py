from flask import Blueprint, request, jsonify, send_file
import os
import json
import uuid
import shutil
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

deployment_manager_bp = Blueprint('deployment_manager', __name__)

class DeploymentManager:
    def __init__(self, base_path: str = "/home/ubuntu/sebaircode-deployments"):
        self.base_path = base_path
        self.ensure_base_directory()
    
    def ensure_base_directory(self):
        """Ensure the base directory for deployments exists"""
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)
        
        # Create subdirectories
        for subdir in ['apps', 'static', 'backups']:
            subdir_path = os.path.join(self.base_path, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path, exist_ok=True)
    
    def deploy_app(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy an application"""
        try:
            app_id = app_data.get('app_id') or str(uuid.uuid4())
            app_name = app_data.get('app_name', f'app-{app_id}')
            app_type = app_data.get('app_type', 'static')
            files = app_data.get('files', {})
            
            # Create app directory
            app_dir = os.path.join(self.base_path, 'apps', app_id)
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)
            os.makedirs(app_dir, exist_ok=True)
            
            # Write files to app directory
            for file_path, file_content in files.items():
                full_path = os.path.join(app_dir, file_path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write file content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
            
            # Generate deployment configuration
            deployment_config = {
                'app_id': app_id,
                'app_name': app_name,
                'app_type': app_type,
                'app_dir': app_dir,
                'deployed_at': datetime.now().isoformat(),
                'status': 'deployed',
                'url': f"https://{app_id}.sebaircode.com",
                'subdomain': app_id,
                'files': list(files.keys())
            }
            
            # Save deployment metadata
            self._save_deployment_metadata(app_id, deployment_config)
            
            # For static apps, copy to static directory for serving
            if app_type in ['static', 'simple_website']:
                static_dir = os.path.join(self.base_path, 'static', app_id)
                if os.path.exists(static_dir):
                    shutil.rmtree(static_dir)
                shutil.copytree(app_dir, static_dir)
            
            # For React apps, build and deploy
            elif app_type == 'react_app':
                build_result = self._build_react_app(app_dir, app_id)
                if not build_result['success']:
                    return build_result
                deployment_config.update(build_result)
            
            return {
                'success': True,
                'deployment': deployment_config
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_react_app(self, app_dir: str, app_id: str) -> Dict[str, Any]:
        """Build a React application"""
        try:
            # Install dependencies
            install_result = subprocess.run(
                ['npm', 'install'],
                cwd=app_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if install_result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Failed to install dependencies: {install_result.stderr}'
                }
            
            # Build the app
            build_result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd=app_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if build_result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Failed to build app: {build_result.stderr}'
                }
            
            # Copy build files to static directory
            build_dir = os.path.join(app_dir, 'build')
            static_dir = os.path.join(self.base_path, 'static', app_id)
            
            if os.path.exists(static_dir):
                shutil.rmtree(static_dir)
            
            if os.path.exists(build_dir):
                shutil.copytree(build_dir, static_dir)
            else:
                # Try 'dist' directory (for Vite builds)
                dist_dir = os.path.join(app_dir, 'dist')
                if os.path.exists(dist_dir):
                    shutil.copytree(dist_dir, static_dir)
                else:
                    return {
                        'success': False,
                        'error': 'Build directory not found'
                    }
            
            return {
                'success': True,
                'build_output': build_result.stdout,
                'static_dir': static_dir
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Build process timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_deployment_metadata(self, app_id: str, metadata: Dict[str, Any]):
        """Save deployment metadata"""
        metadata_path = os.path.join(self.base_path, 'apps', app_id, 'deployment.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def get_deployment_info(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment information"""
        try:
            metadata_path = os.path.join(self.base_path, 'apps', app_id, 'deployment.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception:
            return None
    
    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployments"""
        deployments = []
        
        try:
            apps_dir = os.path.join(self.base_path, 'apps')
            for app_id in os.listdir(apps_dir):
                deployment_info = self.get_deployment_info(app_id)
                if deployment_info:
                    deployments.append(deployment_info)
        except Exception:
            pass
        
        return deployments
    
    def delete_deployment(self, app_id: str) -> Dict[str, Any]:
        """Delete a deployment"""
        try:
            app_dir = os.path.join(self.base_path, 'apps', app_id)
            static_dir = os.path.join(self.base_path, 'static', app_id)
            
            # Remove app directory
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)
            
            # Remove static directory
            if os.path.exists(static_dir):
                shutil.rmtree(static_dir)
            
            return {
                'success': True,
                'message': 'Deployment deleted successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_deployment(self, app_id: str, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing deployment"""
        try:
            # Get existing deployment info
            existing_deployment = self.get_deployment_info(app_id)
            if not existing_deployment:
                return {
                    'success': False,
                    'error': 'Deployment not found'
                }
            
            # Create backup before update
            backup_result = self.backup_deployment(app_id)
            if not backup_result['success']:
                return backup_result
            
            # Update with new data
            app_data['app_id'] = app_id
            result = self.deploy_app(app_data)
            
            if result['success']:
                result['deployment']['updated_at'] = datetime.now().isoformat()
                result['deployment']['backup_created'] = backup_result['backup_path']
                self._save_deployment_metadata(app_id, result['deployment'])
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def backup_deployment(self, app_id: str) -> Dict[str, Any]:
        """Create a backup of a deployment"""
        try:
            app_dir = os.path.join(self.base_path, 'apps', app_id)
            if not os.path.exists(app_dir):
                return {
                    'success': False,
                    'error': 'Deployment not found'
                }
            
            backup_filename = f"{app_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(self.base_path, 'backups', backup_filename)
            
            # Create backup
            shutil.copytree(app_dir, backup_path)
            
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

class DomainManager:
    """Manage custom domains and subdomains"""
    
    def __init__(self, base_domain: str = "sebaircode.com"):
        self.base_domain = base_domain
        self.domains_file = "/home/ubuntu/sebaircode-deployments/domains.json"
        self.ensure_domains_file()
    
    def ensure_domains_file(self):
        """Ensure domains file exists"""
        if not os.path.exists(self.domains_file):
            with open(self.domains_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
    
    def register_subdomain(self, app_id: str, subdomain: str) -> Dict[str, Any]:
        """Register a subdomain for an app"""
        try:
            # Load existing domains
            with open(self.domains_file, 'r', encoding='utf-8') as f:
                domains = json.load(f)
            
            # Check if subdomain is already taken
            for existing_app_id, domain_info in domains.items():
                if domain_info.get('subdomain') == subdomain:
                    return {
                        'success': False,
                        'error': 'Subdomain already taken'
                    }
            
            # Register subdomain
            full_domain = f"{subdomain}.{self.base_domain}"
            domains[app_id] = {
                'subdomain': subdomain,
                'full_domain': full_domain,
                'registered_at': datetime.now().isoformat(),
                'type': 'subdomain'
            }
            
            # Save domains
            with open(self.domains_file, 'w', encoding='utf-8') as f:
                json.dump(domains, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'domain': full_domain,
                'subdomain': subdomain
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def register_custom_domain(self, app_id: str, custom_domain: str) -> Dict[str, Any]:
        """Register a custom domain for an app"""
        try:
            # Load existing domains
            with open(self.domains_file, 'r', encoding='utf-8') as f:
                domains = json.load(f)
            
            # Update domain info
            if app_id not in domains:
                domains[app_id] = {}
            
            domains[app_id].update({
                'custom_domain': custom_domain,
                'custom_domain_registered_at': datetime.now().isoformat(),
                'custom_domain_verified': False
            })
            
            # Save domains
            with open(self.domains_file, 'w', encoding='utf-8') as f:
                json.dump(domains, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'custom_domain': custom_domain,
                'verification_required': True,
                'dns_instructions': {
                    'type': 'CNAME',
                    'name': custom_domain,
                    'value': f"{app_id}.{self.base_domain}"
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_domain_info(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Get domain information for an app"""
        try:
            with open(self.domains_file, 'r', encoding='utf-8') as f:
                domains = json.load(f)
            return domains.get(app_id)
        except Exception:
            return None

# Initialize managers
deployment_manager = DeploymentManager()
domain_manager = DomainManager()

@deployment_manager_bp.route('/deploy', methods=['POST'])
def deploy_application():
    """Deploy an application"""
    try:
        data = request.get_json()
        result = deployment_manager.deploy_app(data)
        
        # Register subdomain if deployment successful
        if result['success']:
            app_id = result['deployment']['app_id']
            subdomain = result['deployment']['subdomain']
            domain_result = domain_manager.register_subdomain(app_id, subdomain)
            
            if domain_result['success']:
                result['deployment']['domain'] = domain_result['domain']
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@deployment_manager_bp.route('/info/<app_id>', methods=['GET'])
def get_deployment_info(app_id):
    """Get deployment information"""
    try:
        deployment_info = deployment_manager.get_deployment_info(app_id)
        domain_info = domain_manager.get_domain_info(app_id)
        
        if deployment_info:
            if domain_info:
                deployment_info['domain_info'] = domain_info
            
            return jsonify({'success': True, 'data': deployment_info})
        else:
            return jsonify({'success': False, 'error': 'Deployment not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@deployment_manager_bp.route('/list', methods=['GET'])
def list_deployments():
    """List all deployments"""
    try:
        deployments = deployment_manager.list_deployments()
        
        # Add domain info to each deployment
        for deployment in deployments:
            domain_info = domain_manager.get_domain_info(deployment['app_id'])
            if domain_info:
                deployment['domain_info'] = domain_info
        
        return jsonify({'success': True, 'data': deployments})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@deployment_manager_bp.route('/update/<app_id>', methods=['PUT'])
def update_deployment(app_id):
    """Update an existing deployment"""
    try:
        data = request.get_json()
        result = deployment_manager.update_deployment(app_id, data)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@deployment_manager_bp.route('/delete/<app_id>', methods=['DELETE'])
def delete_deployment(app_id):
    """Delete a deployment"""
    try:
        result = deployment_manager.delete_deployment(app_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@deployment_manager_bp.route('/backup/<app_id>', methods=['POST'])
def backup_deployment(app_id):
    """Create a backup of a deployment"""
    try:
        result = deployment_manager.backup_deployment(app_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@deployment_manager_bp.route('/domain/subdomain', methods=['POST'])
def register_subdomain():
    """Register a subdomain"""
    try:
        data = request.get_json()
        app_id = data.get('app_id')
        subdomain = data.get('subdomain')
        
        if not app_id or not subdomain:
            return jsonify({'success': False, 'error': 'app_id and subdomain are required'}), 400
        
        result = domain_manager.register_subdomain(app_id, subdomain)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@deployment_manager_bp.route('/domain/custom', methods=['POST'])
def register_custom_domain():
    """Register a custom domain"""
    try:
        data = request.get_json()
        app_id = data.get('app_id')
        custom_domain = data.get('custom_domain')
        
        if not app_id or not custom_domain:
            return jsonify({'success': False, 'error': 'app_id and custom_domain are required'}), 400
        
        result = domain_manager.register_custom_domain(app_id, custom_domain)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@deployment_manager_bp.route('/domain/info/<app_id>', methods=['GET'])
def get_domain_info(app_id):
    """Get domain information"""
    try:
        domain_info = domain_manager.get_domain_info(app_id)
        
        if domain_info:
            return jsonify({'success': True, 'data': domain_info})
        else:
            return jsonify({'success': False, 'error': 'Domain not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Static file serving for deployed apps
@deployment_manager_bp.route('/serve/<app_id>')
@deployment_manager_bp.route('/serve/<app_id>/<path:filename>')
def serve_deployed_app(app_id, filename='index.html'):
    """Serve deployed application files"""
    try:
        static_dir = os.path.join(deployment_manager.base_path, 'static', app_id)
        
        if not os.path.exists(static_dir):
            return jsonify({'error': 'App not found'}), 404
        
        file_path = os.path.join(static_dir, filename)
        
        # If file doesn't exist, try to serve index.html (for SPA routing)
        if not os.path.exists(file_path):
            index_path = os.path.join(static_dir, 'index.html')
            if os.path.exists(index_path):
                file_path = index_path
            else:
                return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

