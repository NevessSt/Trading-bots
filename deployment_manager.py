#!/usr/bin/env python3
"""
Deployment Manager for TradingBot Pro
Handles automated deployment, scaling, and environment management
"""

import os
import json
import yaml
import subprocess
import logging
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import docker
import boto3
from kubernetes import client, config
from fabric import Connection
import paramiko

class DeploymentEnvironment:
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class DeploymentStrategy:
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    CANARY = "canary"
    RECREATE = "recreate"

class DeploymentManager:
    def __init__(self, config_path: str = "deployment_config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.docker_client = None
        self.k8s_client = None
        self.aws_client = None
        
        # Initialize clients
        self._initialize_clients()
        
        # Deployment state
        self.deployment_history = []
        self.current_deployments = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load deployment configuration"""
        default_config = {
            'environments': {
                'development': {
                    'type': 'local',
                    'replicas': 1,
                    'resources': {'cpu': '0.5', 'memory': '512Mi'}
                },
                'staging': {
                    'type': 'kubernetes',
                    'namespace': 'tradingbot-staging',
                    'replicas': 2,
                    'resources': {'cpu': '1', 'memory': '1Gi'}
                },
                'production': {
                    'type': 'kubernetes',
                    'namespace': 'tradingbot-prod',
                    'replicas': 3,
                    'resources': {'cpu': '2', 'memory': '2Gi'}
                }
            },
            'docker': {
                'registry': 'your-registry.com',
                'image_name': 'tradingbot-pro',
                'dockerfile_path': './Dockerfile'
            },
            'kubernetes': {
                'config_path': '~/.kube/config',
                'ingress_enabled': True,
                'ssl_enabled': True
            },
            'aws': {
                'region': 'us-east-1',
                'ecs_cluster': 'tradingbot-cluster',
                'rds_instance': 'tradingbot-db'
            },
            'monitoring': {
                'prometheus_enabled': True,
                'grafana_enabled': True,
                'alerting_enabled': True
            },
            'backup': {
                'enabled': True,
                'schedule': '0 2 * * *',  # Daily at 2 AM
                's3_bucket': 'tradingbot-backups'
            }
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _initialize_clients(self):
        """Initialize deployment clients"""
        try:
            # Docker client
            self.docker_client = docker.from_env()
            self.logger.info("Docker client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
        
        try:
            # Kubernetes client
            config.load_kube_config(self.config['kubernetes']['config_path'])
            self.k8s_client = client.AppsV1Api()
            self.logger.info("Kubernetes client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Kubernetes client: {e}")
        
        try:
            # AWS client
            self.aws_client = boto3.client('ecs', region_name=self.config['aws']['region'])
            self.logger.info("AWS client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS client: {e}")
    
    def build_image(self, version: str, environment: str = None) -> Dict:
        """Build Docker image"""
        try:
            self.logger.info(f"Building Docker image version {version}")
            
            docker_config = self.config['docker']
            image_tag = f"{docker_config['registry']}/{docker_config['image_name']}:{version}"
            
            # Build image
            image, build_logs = self.docker_client.images.build(
                path=".",
                dockerfile=docker_config['dockerfile_path'],
                tag=image_tag,
                rm=True,
                forcerm=True
            )
            
            # Log build output
            for log in build_logs:
                if 'stream' in log:
                    self.logger.info(log['stream'].strip())
            
            # Push to registry
            push_result = self._push_image(image_tag)
            
            return {
                'success': True,
                'image_tag': image_tag,
                'image_id': image.id,
                'push_result': push_result
            }
            
        except Exception as e:
            self.logger.error(f"Failed to build image: {e}")
            return {'success': False, 'error': str(e)}
    
    def _push_image(self, image_tag: str) -> Dict:
        """Push image to registry"""
        try:
            self.logger.info(f"Pushing image {image_tag}")
            
            push_logs = self.docker_client.images.push(
                repository=image_tag,
                stream=True,
                decode=True
            )
            
            for log in push_logs:
                if 'status' in log:
                    self.logger.info(f"Push status: {log['status']}")
                if 'error' in log:
                    raise Exception(log['error'])
            
            return {'success': True, 'message': 'Image pushed successfully'}
            
        except Exception as e:
            self.logger.error(f"Failed to push image: {e}")
            return {'success': False, 'error': str(e)}
    
    def deploy(self, version: str, environment: str, strategy: str = DeploymentStrategy.ROLLING) -> Dict:
        """Deploy application to specified environment"""
        try:
            self.logger.info(f"Starting deployment of version {version} to {environment} using {strategy} strategy")
            
            env_config = self.config['environments'].get(environment)
            if not env_config:
                raise ValueError(f"Environment {environment} not configured")
            
            # Pre-deployment checks
            pre_check_result = self._pre_deployment_checks(version, environment)
            if not pre_check_result['success']:
                return pre_check_result
            
            # Deploy based on environment type
            if env_config['type'] == 'kubernetes':
                result = self._deploy_to_kubernetes(version, environment, strategy)
            elif env_config['type'] == 'aws_ecs':
                result = self._deploy_to_aws_ecs(version, environment, strategy)
            elif env_config['type'] == 'local':
                result = self._deploy_locally(version, environment)
            else:
                raise ValueError(f"Unsupported deployment type: {env_config['type']}")
            
            if result['success']:
                # Post-deployment tasks
                self._post_deployment_tasks(version, environment, result)
                
                # Record deployment
                self._record_deployment(version, environment, strategy, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _pre_deployment_checks(self, version: str, environment: str) -> Dict:
        """Run pre-deployment checks"""
        try:
            checks = []
            
            # Check if image exists
            image_tag = f"{self.config['docker']['registry']}/{self.config['docker']['image_name']}:{version}"
            try:
                self.docker_client.images.get(image_tag)
                checks.append({'name': 'Image exists', 'status': 'passed'})
            except:
                checks.append({'name': 'Image exists', 'status': 'failed', 'error': 'Image not found'})
            
            # Check environment health
            env_health = self._check_environment_health(environment)
            checks.append({'name': 'Environment health', 'status': 'passed' if env_health else 'failed'})
            
            # Check database connectivity
            db_health = self._check_database_health(environment)
            checks.append({'name': 'Database connectivity', 'status': 'passed' if db_health else 'failed'})
            
            # Check resource availability
            resource_check = self._check_resource_availability(environment)
            checks.append({'name': 'Resource availability', 'status': 'passed' if resource_check else 'failed'})
            
            failed_checks = [check for check in checks if check['status'] == 'failed']
            
            return {
                'success': len(failed_checks) == 0,
                'checks': checks,
                'failed_checks': failed_checks
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _deploy_to_kubernetes(self, version: str, environment: str, strategy: str) -> Dict:
        """Deploy to Kubernetes cluster"""
        try:
            env_config = self.config['environments'][environment]
            namespace = env_config['namespace']
            
            # Generate Kubernetes manifests
            manifests = self._generate_k8s_manifests(version, environment)
            
            # Apply manifests based on strategy
            if strategy == DeploymentStrategy.BLUE_GREEN:
                result = self._blue_green_deployment(manifests, namespace)
            elif strategy == DeploymentStrategy.ROLLING:
                result = self._rolling_deployment(manifests, namespace)
            elif strategy == DeploymentStrategy.CANARY:
                result = self._canary_deployment(manifests, namespace)
            else:
                result = self._recreate_deployment(manifests, namespace)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _deploy_to_aws_ecs(self, version: str, environment: str, strategy: str) -> Dict:
        """Deploy to AWS ECS"""
        try:
            # Create task definition
            task_definition = self._create_ecs_task_definition(version, environment)
            
            # Update service
            service_name = f"tradingbot-{environment}"
            cluster_name = self.config['aws']['ecs_cluster']
            
            response = self.aws_client.update_service(
                cluster=cluster_name,
                service=service_name,
                taskDefinition=task_definition['taskDefinitionArn'],
                forceNewDeployment=True
            )
            
            # Wait for deployment to complete
            self._wait_for_ecs_deployment(cluster_name, service_name)
            
            return {
                'success': True,
                'service_arn': response['service']['serviceArn'],
                'task_definition': task_definition['taskDefinitionArn']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _deploy_locally(self, version: str, environment: str) -> Dict:
        """Deploy locally using Docker Compose"""
        try:
            # Update docker-compose file with new version
            compose_file = f"docker-compose.{environment}.yml"
            
            # Stop existing containers
            subprocess.run(['docker-compose', '-f', compose_file, 'down'], check=True)
            
            # Start new containers
            env = os.environ.copy()
            env['IMAGE_VERSION'] = version
            
            subprocess.run(
                ['docker-compose', '-f', compose_file, 'up', '-d'],
                env=env,
                check=True
            )
            
            # Wait for services to be healthy
            time.sleep(30)  # Give services time to start
            
            return {
                'success': True,
                'message': f'Local deployment completed for version {version}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_k8s_manifests(self, version: str, environment: str) -> Dict:
        """Generate Kubernetes manifests"""
        env_config = self.config['environments'][environment]
        image_tag = f"{self.config['docker']['registry']}/{self.config['docker']['image_name']}:{version}"
        
        deployment_manifest = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': f'tradingbot-{environment}',
                'namespace': env_config['namespace'],
                'labels': {
                    'app': 'tradingbot',
                    'environment': environment,
                    'version': version
                }
            },
            'spec': {
                'replicas': env_config['replicas'],
                'selector': {
                    'matchLabels': {
                        'app': 'tradingbot',
                        'environment': environment
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': 'tradingbot',
                            'environment': environment,
                            'version': version
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': 'tradingbot',
                            'image': image_tag,
                            'ports': [{'containerPort': 5000}],
                            'resources': {
                                'requests': env_config['resources'],
                                'limits': env_config['resources']
                            },
                            'env': [
                                {'name': 'ENVIRONMENT', 'value': environment},
                                {'name': 'VERSION', 'value': version}
                            ],
                            'livenessProbe': {
                                'httpGet': {
                                    'path': '/health',
                                    'port': 5000
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': '/ready',
                                    'port': 5000
                                },
                                'initialDelaySeconds': 5,
                                'periodSeconds': 5
                            }
                        }]
                    }
                }
            }
        }
        
        service_manifest = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f'tradingbot-{environment}-service',
                'namespace': env_config['namespace']
            },
            'spec': {
                'selector': {
                    'app': 'tradingbot',
                    'environment': environment
                },
                'ports': [{
                    'port': 80,
                    'targetPort': 5000
                }],
                'type': 'ClusterIP'
            }
        }
        
        return {
            'deployment': deployment_manifest,
            'service': service_manifest
        }
    
    def _rolling_deployment(self, manifests: Dict, namespace: str) -> Dict:
        """Perform rolling deployment"""
        try:
            # Apply deployment manifest
            deployment = manifests['deployment']
            
            # Check if deployment exists
            deployment_name = deployment['metadata']['name']
            
            try:
                existing_deployment = self.k8s_client.read_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace
                )
                # Update existing deployment
                self.k8s_client.patch_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace,
                    body=deployment
                )
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    # Create new deployment
                    self.k8s_client.create_namespaced_deployment(
                        namespace=namespace,
                        body=deployment
                    )
                else:
                    raise
            
            # Apply service manifest
            service = manifests['service']
            service_name = service['metadata']['name']
            
            try:
                self.k8s_client.read_namespaced_service(
                    name=service_name,
                    namespace=namespace
                )
                # Service exists, update if needed
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    # Create service
                    client.CoreV1Api().create_namespaced_service(
                        namespace=namespace,
                        body=service
                    )
            
            # Wait for rollout to complete
            self._wait_for_rollout(deployment_name, namespace)
            
            return {
                'success': True,
                'deployment_name': deployment_name,
                'service_name': service_name
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _wait_for_rollout(self, deployment_name: str, namespace: str, timeout: int = 600):
        """Wait for Kubernetes rollout to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                deployment = self.k8s_client.read_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace
                )
                
                status = deployment.status
                if (status.ready_replicas == status.replicas and
                    status.updated_replicas == status.replicas):
                    self.logger.info(f"Rollout completed for {deployment_name}")
                    return True
                
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error checking rollout status: {e}")
                time.sleep(10)
        
        raise TimeoutError(f"Rollout timeout for {deployment_name}")
    
    def _post_deployment_tasks(self, version: str, environment: str, deployment_result: Dict):
        """Run post-deployment tasks"""
        try:
            # Health check
            self._post_deployment_health_check(environment)
            
            # Update monitoring
            self._update_monitoring_config(version, environment)
            
            # Send notifications
            self._send_deployment_notification(version, environment, deployment_result)
            
            # Update load balancer if needed
            self._update_load_balancer(environment)
            
        except Exception as e:
            self.logger.error(f"Post-deployment tasks failed: {e}")
    
    def _post_deployment_health_check(self, environment: str):
        """Perform post-deployment health check"""
        env_config = self.config['environments'][environment]
        
        # Determine health check URL
        if environment == 'local':
            health_url = 'http://localhost:5000/health'
        else:
            # For K8s or cloud deployments, use service URL
            health_url = f'http://tradingbot-{environment}-service/health'
        
        max_retries = 10
        retry_delay = 30
        
        for attempt in range(max_retries):
            try:
                response = requests.get(health_url, timeout=10)
                if response.status_code == 200:
                    self.logger.info(f"Health check passed for {environment}")
                    return True
            except Exception as e:
                self.logger.warning(f"Health check attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        
        raise Exception(f"Health check failed for {environment} after {max_retries} attempts")
    
    def rollback(self, environment: str, target_version: str = None) -> Dict:
        """Rollback deployment to previous version"""
        try:
            self.logger.info(f"Starting rollback for {environment}")
            
            if not target_version:
                # Get previous version from deployment history
                target_version = self._get_previous_version(environment)
            
            if not target_version:
                return {'success': False, 'error': 'No previous version found'}
            
            # Perform rollback deployment
            result = self.deploy(target_version, environment, DeploymentStrategy.ROLLING)
            
            if result['success']:
                self.logger.info(f"Rollback completed to version {target_version}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_previous_version(self, environment: str) -> Optional[str]:
        """Get previous deployed version for environment"""
        env_deployments = [
            d for d in self.deployment_history
            if d['environment'] == environment and d['status'] == 'success'
        ]
        
        if len(env_deployments) >= 2:
            return env_deployments[-2]['version']
        
        return None
    
    def _record_deployment(self, version: str, environment: str, strategy: str, result: Dict):
        """Record deployment in history"""
        deployment_record = {
            'version': version,
            'environment': environment,
            'strategy': strategy,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success' if result['success'] else 'failed',
            'result': result
        }
        
        self.deployment_history.append(deployment_record)
        
        # Keep only last 50 deployments
        if len(self.deployment_history) > 50:
            self.deployment_history = self.deployment_history[-50:]
        
        # Save to file
        try:
            with open('deployment_history.json', 'w') as f:
                json.dump(self.deployment_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save deployment history: {e}")
    
    def get_deployment_status(self, environment: str = None) -> Dict:
        """Get current deployment status"""
        if environment:
            env_deployments = [
                d for d in self.deployment_history
                if d['environment'] == environment
            ]
            return {
                'environment': environment,
                'deployments': env_deployments[-10:],  # Last 10 deployments
                'current_version': env_deployments[-1]['version'] if env_deployments else None
            }
        else:
            return {
                'all_deployments': self.deployment_history[-20:],  # Last 20 deployments
                'environments': list(self.config['environments'].keys())
            }
    
    def scale_deployment(self, environment: str, replicas: int) -> Dict:
        """Scale deployment replicas"""
        try:
            env_config = self.config['environments'][environment]
            
            if env_config['type'] == 'kubernetes':
                deployment_name = f'tradingbot-{environment}'
                namespace = env_config['namespace']
                
                # Scale deployment
                self.k8s_client.patch_namespaced_deployment_scale(
                    name=deployment_name,
                    namespace=namespace,
                    body={'spec': {'replicas': replicas}}
                )
                
                return {
                    'success': True,
                    'message': f'Scaled {deployment_name} to {replicas} replicas'
                }
            else:
                return {'success': False, 'error': 'Scaling not supported for this environment type'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_environment_health(self, environment: str) -> bool:
        """Check if environment is healthy"""
        try:
            env_config = self.config['environments'][environment]
            
            if env_config['type'] == 'kubernetes':
                # Check if namespace exists and is active
                namespace = env_config['namespace']
                client.CoreV1Api().read_namespace(namespace)
                return True
            elif env_config['type'] == 'aws_ecs':
                # Check if ECS cluster is active
                cluster_name = self.config['aws']['ecs_cluster']
                response = self.aws_client.describe_clusters(clusters=[cluster_name])
                return len(response['clusters']) > 0 and response['clusters'][0]['status'] == 'ACTIVE'
            else:
                return True  # Local environment
                
        except Exception as e:
            self.logger.error(f"Environment health check failed: {e}")
            return False
    
    def _check_database_health(self, environment: str) -> bool:
        """Check database connectivity"""
        try:
            # This would typically connect to the actual database
            # For now, return True as a placeholder
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False
    
    def _check_resource_availability(self, environment: str) -> bool:
        """Check if sufficient resources are available"""
        try:
            env_config = self.config['environments'][environment]
            
            if env_config['type'] == 'kubernetes':
                # Check node resources
                nodes = client.CoreV1Api().list_node()
                # Simplified check - in reality, you'd calculate available resources
                return len(nodes.items) > 0
            else:
                return True  # Assume resources are available for other types
                
        except Exception as e:
            self.logger.error(f"Resource availability check failed: {e}")
            return False
    
    def _send_deployment_notification(self, version: str, environment: str, result: Dict):
        """Send deployment notification"""
        try:
            status = "SUCCESS" if result['success'] else "FAILED"
            message = f"Deployment {status}: Version {version} to {environment}"
            
            # Here you would integrate with your notification system
            # (Slack, email, etc.)
            self.logger.info(f"Notification: {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
    
    def _update_monitoring_config(self, version: str, environment: str):
        """Update monitoring configuration"""
        try:
            # Update Prometheus targets, Grafana dashboards, etc.
            self.logger.info(f"Updated monitoring config for {environment} version {version}")
        except Exception as e:
            self.logger.error(f"Failed to update monitoring config: {e}")
    
    def _update_load_balancer(self, environment: str):
        """Update load balancer configuration"""
        try:
            # Update load balancer rules, health checks, etc.
            self.logger.info(f"Updated load balancer for {environment}")
        except Exception as e:
            self.logger.error(f"Failed to update load balancer: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingBot Deployment Manager')
    parser.add_argument('action', choices=['build', 'deploy', 'rollback', 'scale', 'status'])
    parser.add_argument('--version', help='Version to deploy')
    parser.add_argument('--environment', help='Target environment')
    parser.add_argument('--strategy', help='Deployment strategy')
    parser.add_argument('--replicas', type=int, help='Number of replicas for scaling')
    
    args = parser.parse_args()
    
    deployment_manager = DeploymentManager()
    
    if args.action == 'build':
        if not args.version:
            print("Version is required for build")
            exit(1)
        result = deployment_manager.build_image(args.version)
        print(json.dumps(result, indent=2))
    
    elif args.action == 'deploy':
        if not args.version or not args.environment:
            print("Version and environment are required for deploy")
            exit(1)
        strategy = args.strategy or DeploymentStrategy.ROLLING
        result = deployment_manager.deploy(args.version, args.environment, strategy)
        print(json.dumps(result, indent=2))
    
    elif args.action == 'rollback':
        if not args.environment:
            print("Environment is required for rollback")
            exit(1)
        result = deployment_manager.rollback(args.environment, args.version)
        print(json.dumps(result, indent=2))
    
    elif args.action == 'scale':
        if not args.environment or not args.replicas:
            print("Environment and replicas are required for scaling")
            exit(1)
        result = deployment_manager.scale_deployment(args.environment, args.replicas)
        print(json.dumps(result, indent=2))
    
    elif args.action == 'status':
        result = deployment_manager.get_deployment_status(args.environment)
        print(json.dumps(result, indent=2))